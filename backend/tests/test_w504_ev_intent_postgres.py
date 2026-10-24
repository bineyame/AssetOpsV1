"""W5-04a V1a: migration `0035_w5_ev_work`, the EV domain contract, the selected EV basis port and EV case links.

`.agent/W5-04-build-spec.md` "V1 migration", "V1 selection, clock and schema" and readiness rulings 2-5, 9, 12.
The EV Finding comes from W2-05b's registered `interrupted` replay through the W2-06 worker (`ev_depth_cases.
settled`); its selection is the real W4 linked-selection pin and the real `EvReadService` reads on the caller's
connection. Direct-SQL rows exercise only DB constraints and the downgrade guard; W4 cases come from the W4 service.
Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import json
from datetime import timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from ev_depth_cases import chain, settled  # noqa: F401 - the W2-05b registered replay fixture
    from test_s1_bindings_postgres import _alembic
    from test_w203_cold_migration_postgres import _replica, head
    from test_w401_work_service_postgres import PRINCIPAL, request

    from assetops_backend.work import domain_action as d
    from assetops_backend.work.adapters import postgres_work_read as wr
    from assetops_backend.work.composition import (_link_read_ports, build_work_service, selected_ev_basis,
                                                   selected_finding_pin)

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
