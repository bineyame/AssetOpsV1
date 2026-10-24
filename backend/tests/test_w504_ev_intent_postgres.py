"""W5-04a V1a/V1b: migration `0035_w5_ev_work`, the EV domain contract, the selected EV basis port, EV case links,
and the EV commands and detail over the real selection (readiness 27, 28, 30, 7).

`.agent/W5-04-build-spec.md` "V1 migration", "V1 selection, clock and schema" and readiness rulings 2-5, 9, 12.
The EV Finding comes from W2-05b's registered `interrupted` replay through the W2-06 worker (`ev_depth_cases.
settled`); its selection is the real W4 linked-selection pin and the real `EvReadService` reads on the caller's
connection. Direct-SQL rows exercise only DB constraints and the downgrade guard; W4 cases come from the W4 service.
Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from ev_depth_cases import HI, LO, add_import, chain, settled  # noqa: F401 - the W2-05b registered replay fixture
    from test_s1_bindings_postgres import _alembic
    from test_w203_cold_migration_postgres import _replica, head
    from test_w206_ev_store_postgres import run_worker, select_exact
    from test_w401_work_service_postgres import ACTOR, PRINCIPAL, request

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.evidence.public_provenance import basis_sha256
    from assetops_backend.work import domain_action as d
    from assetops_backend.work.adapters import postgres_work_read as wr
    from assetops_backend.work.adapters.postgres_domain_action_index import PostgresDomainActionRead
    from assetops_backend.work.adapters.postgres_domain_intent import PostgresDomainIntentStore
    from assetops_backend.work.composition import (_link_read_ports, build_work_service, selected_cold_envelope,
                                                   selected_ev_basis, selected_finding_pin)
    from assetops_backend.work.domain_action_index import DomainActionReadService, parse_index_request
    from assetops_backend.work.domain_intent import DomainIntentService

HEAD = "0035_w5_ev_work"
PARENT = "0034_w5_ev_scenarios"
GRANDPARENT = "0033_w5_cold_work"
REFUSED = "Downgrade of 0035_w5_ev_work refused: EV domain Action rows exist."
TABLES = ("domain_action", "domain_action_intent", "domain_action_case_link")
SHA = "0" * 64

ROOT_INSERT = ("INSERT INTO domain_action (id, tenant_id, site_id, action_no, action_code, domain, origin_finding_id, "
               "origin_finding_revision_id, title, raised_at, actor_kind, actor_id, attestation, idempotency_key, "
               "payload_sha256) VALUES (:id, :t, :s, :no, :code, :dom, :f, :r, 'T', clock_timestamp(), 'SERVICE', "
               "'service:x', 'a', :key, :sha)")
INTENT_INSERT = ("INSERT INTO domain_action_intent (id, tenant_id, site_id, action_id, supersedes_id, declared_at, "
                 "criteria, basis, actor_kind, actor_id, attestation, idempotency_key, payload_sha256) VALUES "
                 "(:id, :t, :s, :a, NULL, clock_timestamp(), CAST(:c AS jsonb), CAST('{}' AS jsonb), 'SERVICE', 's', "
                 "'a', :key, :sha)")
LINK_INSERT = ("INSERT INTO domain_action_case_link (id, tenant_id, site_id, action_id, case_id, case_revision_id, "
               "case_event_id, actor_kind, actor_id, attestation, idempotency_key, payload_sha256) VALUES "
               "(:id, :t, :s, :a, :c, :r, :e, 'SERVICE', 's', 'a', :key, :sha)")
REVISION_COLS = ("CAST(id AS text) AS id, CAST(finding_id AS text) AS finding_id, domain, analytic_id, analytic_run_id, "
                 "assessment_revision_id, episode_start, episode_end, created_at")


def counts(engine) -> list[int]:
    with engine.connect() as c:
        return [c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in TABLES]


def checks(engine) -> dict[str, str]:
    """Every CHECK on `domain_action` and `domain_action_intent`, by actual name, with its normalized definition."""
    with engine.connect() as c:
        return {r[0]: r[1] for r in c.execute(text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE contype = 'c' "
            "AND conrelid IN ('domain_action'::regclass, 'domain_action_intent'::regclass)"))}


def domain_checks(engine) -> dict[str, str]:
    return {k: v for k, v in checks(engine).items() if "domain" in v and "criteria" not in v}


@pytest.fixture()
def ev(chain):  # noqa: F811
    """One `interrupted` EV replay: its newest SUPPORTED EV Finding revision and the composed read ports."""
    built = settled(chain, "interrupted")
    with built.engine.connect() as c:
        row = c.execute(text(
            f"SELECT {REVISION_COLS} FROM finding_revision WHERE site_id = :s AND domain = 'ev_charging' "
            "AND lifecycle = 'SUPPORTED' ORDER BY created_at DESC, id LIMIT 1"), {"s": built.site_id}).first()
    assert row is not None, "the EV replay wrote no SUPPORTED EV Finding revision"
    work = build_work_service(URL)
    yield SimpleNamespace(t=built.tenant_id, s=built.site_id, code=built.site_code, engine=built.engine,
                          built=built, revision=dict(row._mapping), ports=_link_read_ports(), work=work)
    work._store.dispose()


def root_sql(ev, no: int, dom: str = "EV_CHARGING") -> dict:
    return {"id": str(uuid4()), "t": ev.t, "s": ev.s, "no": no, "code": f"ACT-{no:06d}", "dom": dom,
            "f": ev.revision["finding_id"], "r": ev.revision["id"], "key": f"w504-sql-{no}", "sha": SHA}


def rejects(engine, sql: str, params: dict, constraint: str | None = None) -> None:
    with pytest.raises(DBAPIError) as caught:
        with engine.begin() as c:
            c.execute(text(sql), params)
    if constraint is not None:
        assert getattr(getattr(caught.value.orig, "diag", None), "constraint_name", None) == constraint, caught.value


def ev_criteria(n: int) -> str:
    rows = [{"key": k, "label": label, "required_evidence": req} for k, label, req in d.EV_CRITERIA]
    return json.dumps((rows * 2)[:n])


# ---- head, chain and catalog ---------------------------------------------------------------------------------------

def test_sole_head_chain_and_named_checks(ev) -> None:
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [HEAD] and head(ev.engine) == HEAD
    assert script.get_revision(HEAD).down_revision == PARENT
    assert script.get_revision(PARENT).down_revision == GRANDPARENT  # W5-03b's 0034 -> 0033 chain is retained
    # Readiness ruling 3: the generated cold-only CHECK is gone; one named CHECK admits both domains.
    assert domain_checks(ev.engine) == {
        "domain_action_domain_chk": "CHECK ((domain = ANY (ARRAY['COLDCHAIN'::text, 'EV_CHARGING'::text])))"}
    assert checks(ev.engine)["domain_action_intent_criteria_count_chk"] == (
        "CHECK (((jsonb_typeof(criteria) = 'array'::text) AND (jsonb_array_length(criteria) = ANY (ARRAY[3, 4]))))")
    # Pre-flight 7: no new index; the Site index query uses 0033 `domain_action_site_raised`.
    with ev.engine.begin() as c:
        assert set(c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'domain_action'")).scalars()) == {
            "domain_action_pkey", "domain_action_scope", "domain_action_code", "domain_action_no", "domain_action_once",
            "domain_action_site_raised"}
        c.execute(text("SET LOCAL enable_seqscan = off"))
        plan = "\n".join(c.execute(text(
            "EXPLAIN SELECT id FROM domain_action WHERE tenant_id = :t AND site_id = :s AND raised_at >= now() - "
            "interval '7 days' AND raised_at < now() AND recorded_at <= now() ORDER BY raised_at DESC, id"),
            {"t": ev.t, "s": ev.s}).scalars())
    assert "domain_action_site_raised" in plan, plan


def test_domain_dispatch_is_closed() -> None:
    """Pre-flight 9 / readiness 12: two reviewed domains, upper-case Action literals to lower-case Finding literals;
    the read adapter's link mapping is derived from the same table, and nothing else resolves."""
    assert {k: v.finding_domain for k, v in d.DOMAINS.items()} == {"COLDCHAIN": "cold_chain",
                                                                   "EV_CHARGING": "ev_charging"}
    assert wr._FINDING_DOMAIN_OF == {"COLDCHAIN": "cold_chain", "EV_CHARGING": "ev_charging"}
    ev_spec = d.DOMAINS["EV_CHARGING"]
    assert [k for k, _, _ in ev_spec.criteria] == ["WITNESSED_SESSION", "NO_FAULT_RECURRENCE", "NO_SERVICE_REDUCTION"]
    assert ev_spec.initial_results == ("PENDING", "PENDING", "PENDING")
    assert ev_spec.summary == "A complete witnessed session and no repeat fault"
    assert ev_spec.basis_keys[-1] == "session_ids" and "session_ids" not in d.DOMAINS["COLDCHAIN"].basis_keys
    assert len(d.DOMAINS["COLDCHAIN"].criteria) == 4 and d.DOMAINS["COLDCHAIN"].messages is d.MESSAGES
    for bad in (None, "MINIGRID", "ev_charging", "coldchain", 1):
        assert d.spec_of(bad) is None


def test_raw_db_admits_ev_root_and_three_or_four_criteria(ev) -> None:
    """Pre-flight 6: the DB checks structure only (array of 3 or 4); exact per-domain counts are service rules."""
    engine = ev.engine
    rejects(engine, ROOT_INSERT, root_sql(ev, 910001, dom="MINIGRID"), "domain_action_domain_chk")
    root = root_sql(ev, 910002)
    with engine.begin() as c:
        c.execute(text(ROOT_INSERT), root)
    ip = {"t": ev.t, "s": ev.s, "a": root["id"], "sha": SHA}
    for n, key in ((2, "w504-i-0002"), (5, "w504-i-0005"), (0, "w504-i-0000")):
        rejects(engine, INTENT_INSERT, {**ip, "id": str(uuid4()), "c": ev_criteria(n), "key": key},
                "domain_action_intent_criteria_count_chk")
    for n in (3, 4):  # each its own root: one intent root per Action
        other = root_sql(ev, 910010 + n)
        with engine.begin() as c:
            c.execute(text(ROOT_INSERT), other)
            c.execute(text(INTENT_INSERT), {**ip, "a": other["id"], "id": str(uuid4()), "c": ev_criteria(n),
                                            "key": f"w504-i-ok{n}"})
    assert counts(engine) == [3, 2, 0]
    _replica(engine, "DELETE FROM domain_action_intent", "DELETE FROM domain_action")


# ---- downgrade guard -----------------------------------------------------------------------------------------------

def _case(ev, key: str) -> tuple[str, str, str]:
    status, created = ev.work.create_case(ev.t, ev.s, request(key), PRINCIPAL)
    assert status == 201, created
    with ev.engine.connect() as c:
        event = str(c.execute(text("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, id DESC "
                                   "LIMIT 1"), {"c": created["id"]}).scalar_one())
    return created["id"], created["revision"]["id"], event


def test_downgrade_refuses_each_ev_shape_then_restores_cold_check(ev) -> None:
    from alembic import command

    engine = ev.engine
    case_id, revision_id, event_id = _case(ev, "w504-dg-request-01")
    ev.work._store.dispose()

    def shape(no: int, child: str | None) -> str:
        root = root_sql(ev, no)
        with engine.begin() as c:
            c.execute(text(ROOT_INSERT), root)
            if child == "intent":
                c.execute(text(INTENT_INSERT), {"t": ev.t, "s": ev.s, "a": root["id"], "id": str(uuid4()),
                                                "c": ev_criteria(3), "key": f"w504-dg-{no}", "sha": SHA})
            elif child == "link":
                c.execute(text(LINK_INSERT), {"t": ev.t, "s": ev.s, "a": root["id"], "id": str(uuid4()),
                                              "c": case_id, "r": revision_id, "e": event_id, "key": f"w504-dg-{no}",
                                              "sha": SHA})
        return root["id"]

    config = _alembic()
    for no, child, expected in ((920001, None, [1, 0, 0]), (920002, "intent", [1, 1, 0]),
                                (920003, "link", [1, 0, 1])):
        shape(no, child)
        engine.dispose()
        with pytest.raises(DBAPIError, match=REFUSED):
            command.downgrade(config, PARENT)
        assert head(engine) == HEAD and counts(engine) == expected, child
        assert "domain_action_domain_chk" in domain_checks(engine)
        _replica(engine, "DELETE FROM domain_action_case_link", "DELETE FROM domain_action_intent",
                 "DELETE FROM domain_action")
    engine.dispose()
    command.downgrade(config, PARENT)
    assert head(engine) == PARENT
    assert domain_checks(engine) == {"domain_action_domain_chk": "CHECK ((domain = 'COLDCHAIN'::text))"}
    assert checks(engine)["domain_action_intent_criteria_count_chk"] == (
        "CHECK (((jsonb_typeof(criteria) = 'array'::text) AND (jsonb_array_length(criteria) = 4)))")
    engine.dispose()
    command.upgrade(config, "head")
    assert head(engine) == HEAD and list(domain_checks(engine)) == ["domain_action_domain_chk"]


# ---- the selected EV basis port and EV case-link visibility --------------------------------------------------------

def _now(ev):
    with ev.engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)


def test_selected_ev_basis_on_the_caller_connection(ev) -> None:
    """Readiness rulings 5, 6, 9: the W4 pin re-selects the EV snapshot; on it, the exact SUPPORTED Finding revision
    (citations from its own `source_provenance.evidence_ids`), its own public session root, and selected session
    roots mapped to distinct selected revision IDs."""
    known_at = _now(ev)
    basis_of = selected_ev_basis(ev.ports)
    with ev.engine.connect() as c:
        pin = selected_finding_pin(ev.ports)(c, ev.t, ev.s, ev.code, ev.revision, known_at)
        assert pin is not None and pin["analytic_id"] in ev.ports.ev_analytics
        basis = basis_of(c, ev.t, ev.s, ev.code, pin, known_at, ev.revision["id"])
        cited = sorted(str(v) for v in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r"),
            {"r": ev.revision["id"]}).scalars())
        session_revisions = {str(r[0]): str(r[1]) for r in c.execute(text(
            "SELECT CAST(id AS text), CAST(session_id AS text) FROM ev_session_revision WHERE site_id = :s"),
            {"s": ev.s})}
        missing = basis_of(c, ev.t, ev.s, ev.code, pin, known_at, str(uuid4()))
    finding = basis["finding"]
    assert finding["revision_id"] == ev.revision["id"] and finding["lifecycle"] == "SUPPORTED"
    assert finding["evidence_ids"] == cited and cited, "the citation set is the exact revision's cited evidence"
    assert set(cited) <= set(basis["selected_evidence_ids"])
    assert (basis["window_start"], basis["window_end"]) == (pin["window_start"], pin["window_end"])
    assert finding["session_id"] in basis["sessions"], "the Finding's own session is selected at the pin"
    roots, revisions = set(basis["sessions"]), set(basis["sessions"].values())
    assert roots and not roots & revisions, "session roots and selected revision IDs are distinct identities"
    assert all(session_revisions.get(revision) == root for root, revision in basis["sessions"].items())
    assert missing is not None and missing["finding"] is None  # an unselected revision is not substituted


def test_ev_case_link_is_visible_in_w4_selection(ev) -> None:
    """Pre-flight 17 / readiness 12: an explicit link from an EV domain Action resolves its origin `ev_charging`
    revision and a real EV pin on the W4 read (never hidden behind a cold-only filter)."""
    case_id, revision_id, event_id = _case(ev, "w504-link-request-01")
    root = root_sql(ev, 930001)
    with ev.engine.begin() as c:
        c.execute(text(ROOT_INSERT), root)
        c.execute(text(LINK_INSERT), {"t": ev.t, "s": ev.s, "a": root["id"], "id": str(uuid4()), "c": case_id,
                                      "r": revision_id, "e": event_id, "key": "w504-link-0001", "sha": SHA})
    known_at = _now(ev)
    with ev.engine.connect() as c:
        rx = wr._ReadTx(c, ev.t, ev.s, ev.code, known_at, None, ev.ports)
        links = rx.revision_links(revision_id, known_at)["domain_action_links"]
        selections = [x for x in rx.link_selections(revision_id, None, None, known_at) if x["id"] == root["id"]]
    assert links == [{"kind": "DOMAIN_ACTION", "action_id": root["id"], "action_event_id": None,
                      "finding_revision_id": ev.revision["id"]}]
    assert len(selections) == 1 and selections[0]["domain"] == "ev_charging" and selections[0]["lineage"]
    assert selections[0]["pin"] is not None and selections[0]["pin"]["analytic_id"] in ev.ports.ev_analytics
    _replica(ev.engine, "DELETE FROM domain_action_case_link", "DELETE FROM domain_action")


# ---- V1a service / V1b read: EV commands and detail over the real selection (readiness 27, 28, 30, 7) -------------

EV_INVALID = "The EV Action declaration is incomplete or invalid."
EV_LINK = "The declared Finding or session is not selected at this site and cutoff."
EV_CHANGED = "The selected EV work basis changed; reload the Action."


def iso(value) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def ev_service(ev, ev_basis_of=None) -> "DomainIntentService":
    """The composed command path (`build_domain_intent_store`), optionally with a perturbed EV basis reader."""
    return DomainIntentService(PostgresDomainIntentStore(
        URL, pin_of=selected_finding_pin(ev.ports), ev_basis_of=ev_basis_of or selected_ev_basis(ev.ports)))


def ev_reads(ev, ev_basis_of=None) -> "DomainActionReadService":
    ports = ev.ports
    return DomainActionReadService(PostgresDomainActionRead(
        URL, link_rows=build_link_rows_reader(), pin_of=selected_finding_pin(ports),
        envelope_of=selected_cold_envelope(ports), ev_basis_of=ev_basis_of or selected_ev_basis(ports),
        action_window=ports.action_window))


def perturbed(ev, change):
    """The real selected EV basis with one set changed - the deterministic way to make each readiness-30 set differ."""
    real = selected_ev_basis(ev.ports)

    def basis_of(c, t, s, code, pin, known_at, revision_id):
        out = real(c, t, s, code, pin, known_at, revision_id)
        return None if out is None else change(out)

    return basis_of


def selected_now(ev) -> dict:
    known_at = _now(ev)
    with ev.engine.connect() as c:
        pin = selected_finding_pin(ev.ports)(c, ev.t, ev.s, ev.code, ev.revision, known_at)
        assert pin is not None, "the EV Finding revision is not selected now"
        return selected_ev_basis(ev.ports)(c, ev.t, ev.s, ev.code, pin, known_at, ev.revision["id"])


def members(ev) -> tuple[str, list[str]]:
    """The Finding's own session and the evidence IDs valid in all three readiness-30 sets (measured non-empty)."""
    basis = selected_now(ev)
    finding = basis["finding"]
    valid = sorted(set(finding["evidence_ids"]) & set(basis["accepted_evidence_ids"])
                   & set(basis["selected_evidence_ids"]))
    assert finding["session_id"] and valid, "the fixture has no Finding session or no evidence valid in A, B and C"
    return finding["session_id"], valid


def ev_action(ev, key="w504-action-0001", **over) -> dict:
    return {"domain": "EV_CHARGING", "origin_finding_id": ev.revision["finding_id"],
            "origin_finding_revision_id": ev.revision["id"], "title": "Inspect connector c1", "owner_label": None,
            "due_at": None, "raised_at": iso(_now(ev) - timedelta(minutes=10)), "actor": dict(ACTOR),
            "idempotency_key": key, **over}


def ev_intent(ev, sessions, evidence, key="w504-intent-0001", criteria=None, **basis) -> dict:
    rows = [{"key": k, "label": label, "required_evidence": req} for k, label, req in d.EV_CRITERIA]
    return {"supersedes_id": None, "declared_at": iso(_now(ev) - timedelta(minutes=1)),
            "criteria": rows if criteria is None else criteria,
            "basis": {"finding_revision_id": ev.revision["id"], "work_case_id": None, "work_record_id": None,
                      "accepted_evidence_ids": list(evidence), "session_ids": list(sessions), **basis},
            "actor": dict(ACTOR), "idempotency_key": key}


def refused_as(status: int, code: str, message: str, call, *args) -> None:
    with pytest.raises(d.DomainIntentRefused) as caught:
        call(*args)
    assert (caught.value.status, caught.value.code, caught.value.message) == (status, code, message)


def test_ev_action_and_intent_round_trip_with_detail(ev) -> None:
    """Readiness 27/30, build spec "EV closure contract": EV root and intent through the sole writer, exact 200 retries,
    the stored closed basis, and the EV detail (three PENDING results, session revision IDs in provenance)."""
    own, valid = members(ev)
    svc, reads = ev_service(ev), ev_reads(ev)
    try:
        root = ev_action(ev)  # one body: `raised_at` is part of the canonical command hash
        status, created = svc.create_action(ev.t, ev.s, ev.code, root, PRINCIPAL)
        assert status == 201, created
        assert svc.create_action(ev.t, ev.s, ev.code, dict(root), PRINCIPAL) == (200, created)
        aid = created["id"]
        body = ev_intent(ev, [own], valid[:1])
        status, declared = svc.post_intent(ev.t, ev.s, ev.code, aid, body, PRINCIPAL)
        assert status == 201, declared
        assert svc.post_intent(ev.t, ev.s, ev.code, aid, body, PRINCIPAL) == (200, declared)
        assert counts(ev.engine) == [1, 1, 0]
        with ev.engine.connect() as c:
            row = c.execute(text("SELECT a.domain, i.basis, i.criteria FROM domain_action a JOIN domain_action_intent i "
                                 "ON i.action_id = a.id WHERE a.id = :a"), {"a": aid}).one()
        assert row[0] == "EV_CHARGING" and [x["key"] for x in row[2]] == [k for k, _, _ in d.EV_CRITERIA]
        assert row[1] == {"finding_revision_id": ev.revision["id"], "work_case_id": None, "work_record_id": None,
                          "accepted_evidence_ids": valid[:1], "session_ids": [own]}  # no pin key (ruling 27)
        detail = reads.detail(ev.t, ev.s, ev.code, aid, [])
        assert detail["action"]["domain"] == "EV_CHARGING" and detail["action"]["state"] == "OPEN"
        assert detail["intent"]["basis"] == row[1] and detail["intent"]["id"] == declared["intent_id"]
        assert detail["results"] == [{"key": k, "result": "PENDING", "evidence_ids": []} for k, _, _ in d.EV_CRITERIA]
        assert detail["links"]["finding"]["href"] is not None
        assert detail["selection_token"] == declared["selection_token"]
        session_revision = selected_now(ev)["sessions"][own]
        provenance = detail["source_provenance"]
        selected_ids = [aid, ev.revision["id"], declared["intent_id"], session_revision]
        assert provenance["basis_sha256"] == basis_sha256(ev.t, ev.s, selected_ids, provenance["evidence_ids"])
        assert provenance["basis_sha256"] != basis_sha256(ev.t, ev.s, selected_ids + [own], provenance["evidence_ids"])
    finally:
        svc._store.dispose()
        reads._reads.dispose()


def test_ev_create_refusals_write_nothing(ev) -> None:
    """Pre-flight 10/11, readiness 11: neutral unknown domain, a cold body on the EV Site (Site-type mismatch, cold
    literal), a foreign Finding revision (EV literal); no root is written."""
    svc = ev_service(ev)
    try:
        refused_as(422, "DOMAIN_INTENT_INVALID", d.NEUTRAL_DOMAIN_INVALID, svc.create_action, ev.t, ev.s, ev.code,
                   ev_action(ev, domain="MINIGRID"), PRINCIPAL)
        refused_as(422, "DOMAIN_INTENT_LINK_INVALID", d.MESSAGES["DOMAIN_INTENT_LINK_INVALID"], svc.create_action,
                   ev.t, ev.s, ev.code, ev_action(ev, "w504-action-0002", domain="COLDCHAIN"), PRINCIPAL)
        refused_as(422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK, svc.create_action, ev.t, ev.s, ev.code,
                   ev_action(ev, "w504-action-0003", origin_finding_revision_id=str(uuid4())), PRINCIPAL)
        assert counts(ev.engine) == [0, 0, 0]
    finally:
        svc._store.dispose()


def test_ev_intent_refusal_order_and_membership(ev) -> None:
    """Readiness 28 order (neutral shape, 404, EV shape, EV link) and readiness 7/30 membership with no silent
    intersection: each refusal leaves only the Action root."""
    own, valid = members(ev)
    x = valid[0]
    svc = ev_service(ev)
    try:
        aid = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev), PRINCIPAL)[1]["id"]
        unknown = str(uuid4())
        rows = [{"key": k, "label": label, "required_evidence": req} for k, label, req in d.EV_CRITERIA]
        two = ev_intent(ev, [own], [x], criteria=rows[:2])
        no_sessions = ev_intent(ev, [own], [x])
        del no_sessions["basis"]["session_ids"]

        def post(service, action_id, body):
            return service.post_intent(ev.t, ev.s, ev.code, action_id, body, PRINCIPAL)

        refused_as(422, "DOMAIN_INTENT_INVALID", d.NEUTRAL_INTENT_INVALID, post, svc, unknown,
                   {**two, "declared_at": "not-an-instant"})
        for body in (two, no_sessions):
            refused_as(404, "ACTION_NOT_FOUND", d.MESSAGES["ACTION_NOT_FOUND"], post, svc, unknown, body)
            refused_as(422, "DOMAIN_INTENT_INVALID", EV_INVALID, post, svc, aid, body)
        cold_rows = [{"key": k, "label": label, "required_evidence": req} for k, label, req in d.CRITERIA]
        refused_as(422, "DOMAIN_INTENT_INVALID", EV_INVALID, post, svc, aid, ev_intent(ev, [own], [x], criteria=cold_rows))
        refused_as(422, "DOMAIN_INTENT_INVALID", EV_INVALID, post, svc, aid, ev_intent(ev, [], [x]))
        foreign = str(uuid4())
        for body in (ev_intent(ev, [own], [x], finding_revision_id=str(uuid4())),
                     ev_intent(ev, [own, foreign], [x]), ev_intent(ev, [foreign], [x]),
                     ev_intent(ev, [own], [x, foreign])):
            refused_as(422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK, post, svc, aid, body)
        # Readiness 30: a valid ID made absent from exactly one set - A (accepted, not head-cited ... and the
        # converse), B, the exact Finding's citations - and the Finding's own session missing from the declaration.
        drops = (lambda b: {**b, "accepted_evidence_ids": [e for e in b["accepted_evidence_ids"] if e != x]},
                 lambda b: {**b, "selected_evidence_ids": [e for e in b["selected_evidence_ids"] if e != x]},
                 lambda b: {**b, "finding": {**b["finding"],
                                             "evidence_ids": [e for e in b["finding"]["evidence_ids"] if e != x]}},
                 lambda b: {**b, "sessions": {**b["sessions"], foreign: str(uuid4())}})
        for change, sessions in zip(drops, ([own], [own], [own], [foreign])):
            other = ev_service(ev, perturbed(ev, change))
            try:
                refused_as(422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK, post, other, aid, ev_intent(ev, sessions, [x]))
            finally:
                other._store.dispose()
        assert counts(ev.engine) == [1, 0, 0]
        assert post(svc, aid, ev_intent(ev, [own.upper()], [x.upper()]))[0] == 201  # case-normalized membership
    finally:
        svc._store.dispose()


def test_ev_pin_is_immutable_across_later_evidence_and_heads(ev) -> None:
    """Readiness 27: historical reads before/after the intent, a BACKDATED accepted disposition (readiness 55: decided
    on the replay's virtual clock, earlier than the intent's `recorded_at`), a later
    selected head and a foreign requested index window never move the intent's revision, window or basis; an exact
    retry stays 200; a missing or changed exact selection is 409 with the EV message."""
    own, valid = members(ev)
    svc, reads = ev_service(ev), ev_reads(ev)
    try:
        aid = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev), PRINCIPAL)[1]["id"]
        body = ev_intent(ev, [own], valid)
        status, declared = svc.post_intent(ev.t, ev.s, ev.code, aid, body, PRINCIPAL)
        assert status == 201, declared
        recorded = datetime.fromisoformat(declared["recorded_at"].replace("Z", "+00:00"))
        before = reads.detail(ev.t, ev.s, ev.code, aid, [iso(recorded - timedelta(microseconds=1))])
        at = reads.detail(ev.t, ev.s, ev.code, aid, [iso(recorded)])
        assert before["intent"] is None and before["results"] is None and before["status"] == "HISTORICAL"
        assert at["intent"]["id"] == declared["intent_id"] and at["status"] == "HISTORICAL"
        # BACKDATED fixture (readiness 55): the replay's virtual 2026-10-06 decision clock makes this inserted
        # ACCEPTED disposition `decided_at < intent.recorded_at`; it is not a production late decision (see
        # `test_ev_db_time_disposition_after_the_intent_leaves_the_pin_fixed` for the genuine one).
        add_import(ev.built, "41.5")
        assert svc.post_intent(ev.t, ev.s, ev.code, aid, body, PRINCIPAL) == (200, declared)
        late = reads.detail(ev.t, ev.s, ev.code, aid, [])
        assert late["intent"]["basis"] == at["intent"]["basis"] and late["selection_token"] == declared["selection_token"]
        run_worker(ev.built)
        select_exact(ev.built, LO, HI)  # a later selected head of the same window
        later = reads.detail(ev.t, ev.s, ev.code, aid, [])
        assert later["intent"]["basis"] == at["intent"]["basis"]
        assert later["links"]["finding"]["href"] == at["links"]["finding"]["href"]
        assert reads.detail(ev.t, ev.s, ev.code, aid, [iso(recorded)])["selection_token"] == at["selection_token"]
        now = _now(ev)
        index = reads.index(ev.t, ev.s, ev.code, parse_index_request(
            iso(now - timedelta(days=1)), iso(now + timedelta(hours=1)), None, [], None))
        row = next(r for r in index["rows"] if r["action_id"] == aid)
        assert (row["domain"], row["state"], row["criterion_summary"]) == (
            "EV_CHARGING", "OPEN", "A complete witnessed session and no repeat fault")
        foreign = reads.index(ev.t, ev.s, ev.code, parse_index_request(iso(LO), iso(HI), None, [], None))
        assert all(r["action_id"] != aid for r in foreign["rows"])
        assert reads.detail(ev.t, ev.s, ev.code, aid, [])["intent"]["basis"] == at["intent"]["basis"]
    finally:
        svc._store.dispose()
        reads._reads.dispose()
    for change in (lambda b: {**b, "sessions": {}}, lambda b: {**b, "finding": None},
                   lambda b: {**b, "selected_evidence_ids": []}):
        broken = ev_reads(ev, perturbed(ev, change))
        try:
            with pytest.raises(d.DomainIntentRefused) as caught:
                broken.detail(ev.t, ev.s, ev.code, aid, [])
            assert (caught.value.status, caught.value.code, caught.value.message) == (
                409, "DOMAIN_INTENT_BASIS_CHANGED", EV_CHANGED)
        finally:
            broken._reads.dispose()


def test_ev_detail_without_intent_and_unselected_finding_is_unknown(ev) -> None:
    """Q7 (recorded): with no intent a missing selection is not a refusal - status UNKNOWN, no Finding href,
    missing lineage; never a substituted head."""
    svc = ev_service(ev)
    try:
        aid = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev), PRINCIPAL)[1]["id"]
    finally:
        svc._store.dispose()
    blind = ev_reads(ev, perturbed(ev, lambda b: {**b, "finding": None}))
    try:
        detail = blind.detail(ev.t, ev.s, ev.code, aid, [])
    finally:
        blind._reads.dispose()
    assert (detail["intent"], detail["results"], detail["status"]) == (None, None, "UNKNOWN")
    assert detail["links"]["finding"]["href"] is None and detail["source_provenance"]["state"] == "UNKNOWN"


def test_rejected_disposition_advances_the_shared_cutoff_without_accepted_evidence(ev) -> None:
    """Readiness 32: the shared cutoff is max(ingestion_disposition.decided_at) with no `decision = 'ACCEPTED'`
    predicate. A REJECTED disposition decided after the replay's accepted ones advances it; the accepted set, the
    selected basis and a stored EV intent basis never gain the rejection's ID, an intent declaring it is refused with
    no write, and the EV pin, the EV snapshot and the W4 linked selection all read the same advanced cutoff."""
    own, valid = members(ev)
    x = valid[0]
    k0_now = _now(ev)
    with ev.engine.connect() as c:
        pin0 = selected_finding_pin(ev.ports)(c, ev.t, ev.s, ev.code, ev.revision, k0_now)
        assert pin0 is not None
        k0 = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                       {"s": ev.s}).scalar_one()
        assert c.execute(text("SELECT count(*) FROM ingestion_disposition WHERE site_id = :s AND decision = 'ACCEPTED'"),
                         {"s": ev.s}).scalar_one() > 0
    assert pin0["evidence_cutoff"] == k0
    basis0 = selected_now(ev)
    assert basis0["accepted_evidence_ids"] and basis0["selected_evidence_ids"]

    rejection = str(uuid4())
    with ev.engine.begin() as c:
        batch = c.execute(text("SELECT batch_id FROM ingestion_disposition WHERE site_id = :s "
                               "ORDER BY decided_at DESC, ordinal DESC LIMIT 1"), {"s": ev.s}).scalar_one()
        ordinal = c.execute(text("SELECT max(ordinal) + 1 FROM ingestion_disposition WHERE batch_id = :b"),
                            {"b": batch}).scalar_one()
        message = f"w504-rejected-{rejection}"
        c.execute(text(
            "INSERT INTO evidence_rejection (id, tenant_id, site_id, batch_id, ordinal, message_id, kind, field, "
            "detail, envelope_sha256, conflicts_with_evidence_id, received_at) VALUES (:id, :t, :s, :b, :o, :m, "
            "'SCHEMA_INVALID', 'value', 'w504 readiness 32 rejected envelope', :sha, NULL, clock_timestamp())"),
            {"id": rejection, "t": ev.t, "s": ev.s, "b": batch, "o": ordinal, "m": message, "sha": "a" * 64})
        c.execute(text(
            "INSERT INTO ingestion_disposition (batch_id, ordinal, tenant_id, site_id, message_id, decision, "
            "accepted_evidence_id, rejection_id, decided_at) VALUES (:b, :o, :t, :s, :m, 'REJECTED', NULL, :id, "
            "clock_timestamp())"),
            {"id": rejection, "t": ev.t, "s": ev.s, "b": batch, "o": ordinal, "m": message})
    with ev.engine.connect() as c:
        k1 = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                       {"s": ev.s}).scalar_one()
        assert c.execute(text("SELECT decision FROM ingestion_disposition WHERE decided_at = :k AND site_id = :s"),
                         {"k": k1, "s": ev.s}).scalars().all() == ["REJECTED"]
    assert k1 > k0, "the rejected disposition advances the shared watermark"

    now = _now(ev)
    with ev.engine.connect() as c:
        pin1 = selected_finding_pin(ev.ports)(c, ev.t, ev.s, ev.code, ev.revision, now)
        assert pin1 is not None and pin1["evidence_cutoff"] == k1, "the EV pin reads the advanced cutoff"
        assert {k: v for k, v in pin1.items() if k != "evidence_cutoff"} == {
            k: v for k, v in pin0.items() if k != "evidence_cutoff"}, "the same exact window and selection"
        snap = ev.ports.ev_snapshot(c, ev.t, ev.s, ev.code, pin1["window_start"], pin1["window_end"],
                                    pin1["evidence_cutoff"], selection_cutoff=now,
                                    selection_seqs=dict(pin1["selection_seqs"]))
        assert snap["known"] == snap["watermark"] == k1, "the EV snapshot reads the same cutoff"
        basis1 = selected_ev_basis(ev.ports)(c, ev.t, ev.s, ev.code, pin1, now, ev.revision["id"])
    assert basis1["accepted_evidence_ids"] == basis0["accepted_evidence_ids"]
    assert basis1["selected_evidence_ids"] == basis0["selected_evidence_ids"]
    assert basis1["finding"] == basis0["finding"] and basis1["sessions"] == basis0["sessions"]
    assert all(rejection not in ids for ids in (basis1["accepted_evidence_ids"], basis1["selected_evidence_ids"],
                                                 basis1["finding"]["evidence_ids"]))

    svc = ev_service(ev)
    try:
        aid = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev), PRINCIPAL)[1]["id"]
        refused_as(422, "DOMAIN_INTENT_LINK_INVALID", EV_LINK, svc.post_intent, ev.t, ev.s, ev.code, aid,
                   ev_intent(ev, [own], [x, rejection]), PRINCIPAL)
        assert counts(ev.engine) == [1, 0, 0], "the refused rejected-ID declaration writes nothing"
        status, declared = svc.post_intent(ev.t, ev.s, ev.code, aid, ev_intent(ev, [own], valid), PRINCIPAL)
        assert status == 201, declared
    finally:
        svc._store.dispose()
    with ev.engine.connect() as c:
        stored = c.execute(text("SELECT CAST(basis AS text) FROM domain_action_intent WHERE action_id = :a"),
                           {"a": aid}).scalar_one()
    assert x in stored.lower() and rejection not in stored.lower(), "the stored EV basis never cites the rejection"

    case_id, revision_id, event_id = _case(ev, "w504-rejected-cutoff-01")
    with ev.engine.begin() as c:
        c.execute(text(LINK_INSERT), {"t": ev.t, "s": ev.s, "a": aid, "id": str(uuid4()), "c": case_id,
                                      "r": revision_id, "e": event_id, "key": "w504-rejected-link-01", "sha": SHA})
    now = _now(ev)
    with ev.engine.connect() as c:
        rx = wr._ReadTx(c, ev.t, ev.s, ev.code, now, None, ev.ports)
        selections = [s for s in rx.link_selections(revision_id, None, None, now) if s["id"] == aid]
    assert len(selections) == 1 and selections[0]["pin"] is not None
    assert selections[0]["pin"]["evidence_cutoff"] == k1, "the W4 linked selection reads the same cutoff"


def _later_head(ev) -> None:
    """A later selected head of the E window (as the existing immutability vector): import, worker, exact selection."""
    add_import(ev.built, "41.5")
    run_worker(ev.built)
    select_exact(ev.built, LO, HI)


def _index(reads, ev, known_at=None, limit=None, cursor=None) -> dict:
    if not hasattr(ev, "window"):  # one fixed window so a cursor stays valid across pages
        now = _now(ev)
        ev.window = (iso(now - timedelta(days=1)), iso(now + timedelta(hours=1)))
    return reads.index(ev.t, ev.s, ev.code, parse_index_request(
        ev.window[0], ev.window[1], None if limit is None else str(limit),
        [] if known_at is None else [iso(known_at)], cursor))




def test_ev_index_row_uses_the_intent_pin_and_no_intent_row_reads_known_at(ev) -> None:
    """Readiness 53: after a later selected head, an intent-bearing EV index row keeps its exact Finding href and
    contributes CURRENT (as its detail does); the no-intent EV row's href is null and the envelope UNKNOWN; historical
    reads before/after the intent keep the live pin; the cursor fence of the displaced snapshot still pages."""
    own, valid = members(ev)
    svc, reads = ev_service(ev), ev_reads(ev)
    try:
        with_intent = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev, "w504-idx-a"), PRINCIPAL)[1]["id"]
        no_intent = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev, "w504-idx-b"), PRINCIPAL)[1]["id"]
        _, declared = svc.post_intent(ev.t, ev.s, ev.code, with_intent, ev_intent(ev, [own], valid), PRINCIPAL)
        recorded = datetime.fromisoformat(declared["recorded_at"].replace("Z", "+00:00"))
        live = f"/sites/{ev.code}/findings/{ev.revision['finding_id']}?revision_id={ev.revision['id']}"
        before = _index(reads, ev)
        assert [r["origin"]["href"] for r in before["rows"]] == [live, live] and before["status"] == "CURRENT"
        mid = _now(ev)  # after the intent, before the later head
        _later_head(ev)
        after = _index(reads, ev)
        rows = {r["action_id"]: r for r in after["rows"]}
        assert rows[with_intent]["origin"]["href"] == live, "resolved at the intent's pin, not the read known_at"
        assert rows[no_intent]["origin"]["href"] is None and rows[no_intent]["criterion_summary"] is None
        assert rows[with_intent]["criterion_summary"] == "A complete witnessed session and no repeat fault"
        assert after["status"] == "UNKNOWN", "only the no-intent row's unavailable source contributes UNKNOWN"
        assert reads.detail(ev.t, ev.s, ev.code, with_intent, [])["links"]["finding"]["href"] == live
        assert reads.detail(ev.t, ev.s, ev.code, no_intent, [])["links"]["finding"]["href"] is None
        # Historical reads: before the intent (no intent yet: read known_at), at it, and between intent and head.
        for known, expect_intent in ((recorded - timedelta(microseconds=1), False), (recorded, True), (mid, True)):
            hist = _index(reads, ev, known)
            by_id = {r["action_id"]: r for r in hist["rows"]}
            assert {r["origin"]["href"] for r in by_id.values()} == {live} and hist["status"] == "HISTORICAL", known
            assert (by_id[with_intent]["criterion_summary"] is not None) is expect_intent
        # The full-set fence is consistent over the displaced snapshot: both pages succeed and cover both rows.
        first = _index(reads, ev, limit=1)
        assert first["next_cursor"] is not None
        second = _index(reads, ev, limit=1, cursor=first["next_cursor"])
        assert {r["action_id"] for r in first["rows"] + second["rows"]} == {with_intent, no_intent}
        assert first["selection_token"] == second["selection_token"]
    finally:
        svc._store.dispose()
        reads._reads.dispose()


def test_ev_conflict_paths_are_409_with_the_ev_literal_and_write_nothing(ev) -> None:
    """Review L1: every `DOMAIN_INTENT_CONFLICT`/`BASIS_CHANGED` path of the sole writer on an EV Site - same Action key
    with another body, same intent key with another body, a second root intent, a stale `supersedes_id`, a repeated
    exact case link under another key, and a reused link key with another body - is 409 with the EV literal."""
    own, valid = members(ev)
    conflict = "This Action declaration has a newer version; reload it."
    svc = ev_service(ev)

    def post(call, *args):
        return call(ev.t, ev.s, ev.code, *args, PRINCIPAL)

    try:
        root = ev_action(ev)
        status, created = post(svc.create_action, root)
        assert status == 201
        aid = created["id"]
        refused_as(409, "DOMAIN_INTENT_CONFLICT", conflict, post, svc.create_action, {**root, "title": "Other title"})
        assert counts(ev.engine) == [1, 0, 0]
        body = ev_intent(ev, [own], valid)
        status, first = post(svc.post_intent, aid, body)
        assert status == 201
        refused_as(409, "DOMAIN_INTENT_CONFLICT", conflict, post, svc.post_intent, aid,
                   {**body, "declared_at": iso(_now(ev) - timedelta(minutes=2))})
        refused_as(409, "DOMAIN_INTENT_CONFLICT", conflict, post, svc.post_intent, aid,
                   ev_intent(ev, [own], valid, key="w504-intent-second-root"))
        stale = {**ev_intent(ev, [own], valid, key="w504-intent-stale"), "supersedes_id": str(uuid4())}
        refused_as(409, "DOMAIN_INTENT_CONFLICT", conflict, post, svc.post_intent, aid, stale)
        assert counts(ev.engine) == [1, 1, 0]
        status, second = post(svc.post_intent, aid, {**ev_intent(ev, [own], valid, key="w504-intent-v2"),
                                                     "supersedes_id": first["intent_id"]})
        assert status == 201
        refused_as(409, "DOMAIN_INTENT_CONFLICT", conflict, post, svc.post_intent, aid,
                   {**ev_intent(ev, [own], valid, key="w504-intent-v3"), "supersedes_id": first["intent_id"]})
        assert counts(ev.engine) == [1, 2, 0]
        case_id, revision_id, event_id = _case(ev, "w504-conflict-case-01")
        link = {"case_id": case_id, "case_revision_id": revision_id, "case_event_id": event_id,
                "actor": dict(ACTOR), "idempotency_key": "w504-link-01"}
        assert post(svc.post_case_link, aid, link)[0] == 201
        refused_as(409, "DOMAIN_INTENT_CONFLICT", conflict, post, svc.post_case_link, aid,
                   {**link, "idempotency_key": "w504-link-02"})
        other, other_revision, other_event = _case(ev, "w504-conflict-case-02")
        refused_as(409, "DOMAIN_INTENT_BASIS_CHANGED", EV_CHANGED, post, svc.post_case_link, aid,
                   {**link, "case_id": other, "case_revision_id": other_revision, "case_event_id": other_event})
        assert counts(ev.engine) == [1, 2, 1]
        assert second["intent_id"] != first["intent_id"]
    finally:
        svc._store.dispose()


def test_ev_db_time_disposition_after_the_intent_leaves_the_pin_fixed(ev) -> None:
    """Readiness 55: a genuinely late decision (`decided_at` = DB time, after `intent.recorded_at`) never changes the
    intent's exact revision, window, basis, status, token or evidence cutoff. Contrast: the replay-clock vector
    in `test_ev_pin_is_immutable_across_later_evidence_and_heads` is backdated, so its PENDING state is not proof."""
    own, valid = members(ev)
    svc, reads = ev_service(ev), ev_reads(ev)
    try:
        aid = svc.create_action(ev.t, ev.s, ev.code, ev_action(ev), PRINCIPAL)[1]["id"]
        status, declared = svc.post_intent(ev.t, ev.s, ev.code, aid, ev_intent(ev, [own], valid), PRINCIPAL)
        assert status == 201
        recorded = datetime.fromisoformat(declared["recorded_at"].replace("Z", "+00:00"))

        def pin_at(known_at):
            with ev.engine.connect() as c:
                return selected_finding_pin(ev.ports)(c, ev.t, ev.s, ev.code, ev.revision, known_at)

        pin0, detail0 = pin_at(recorded), reads.detail(ev.t, ev.s, ev.code, aid, [])
        add_import(ev.built, "41.5", db_time=True)
        with ev.engine.connect() as c:
            decided = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                                {"s": ev.s}).scalar_one()
        assert decided > recorded, "the inserted disposition is decided after the intent (DB time)"
        pin1, detail1 = pin_at(recorded), reads.detail(ev.t, ev.s, ev.code, aid, [])
        keep = lambda pin: {k: v for k, v in pin.items() if k != "state"}  # noqa: E731 - see the state note below
        assert keep(pin1) == keep(pin0) and pin0["evidence_cutoff"] <= recorded
        # The read at `recorded` is now historical against the advanced watermark: only the pin's own `state` word
        # moves (CURRENT -> HISTORICAL); revision, window, seqs and evidence cutoff are fixed.
        assert (pin0["state"], pin1["state"]) == ("CURRENT", "HISTORICAL")
        assert pin_at(_now(ev))["evidence_cutoff"] == decided > pin0["evidence_cutoff"], "the shared cutoff did advance"
        for key in ("status", "selection_token", "intent", "results", "source_provenance", "links"):
            assert detail1[key] == detail0[key], key
        run_worker(ev.built)
        select_exact(ev.built, LO, HI)
        detail2 = reads.detail(ev.t, ev.s, ev.code, aid, [])
        assert detail2["intent"] == detail0["intent"] and detail2["selection_token"] == detail0["selection_token"]
    finally:
        svc._store.dispose()
        reads._reads.dispose()
