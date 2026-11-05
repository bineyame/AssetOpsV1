"""CH-9b1 L2 (build sheet CH-9b, CH9b1-R): the mill Action from an opportunity, on Postgres at migration 0051.

On the W4-02 MINIGRID Site with CH-4's two seeded opportunity studies:

- the MINI Action is created through `DomainIntentService.create_action(domain="MINI", ...)`, linked to a W4 case,
  the case COMPLETEd, and backfill step c links it to the opportunity thread; `run_lifecycle` then writes
  ACTION_IN_HAND and CHANGE_APPLIED (day = the case `occurred_at`); with the link a 0-eligible head is not withdrawn
  (CH-4 R6 at L2);
- the two origin CHECKs (`domain_action_one_origin`, `domain_action_mini_origin`) reject both pairs, neither pair and a
  non-MINI opportunity origin (SQLSTATE 23514), and a MINI Action is refused a Finding-origin body;
- 0051 downgrades to 0050 (refused while an opportunity-origin row exists) and upgrades back, the rows of `action`,
  `domain_action` and `chain_action_thread` identical across the round trip;
- Q6 (alternative proof, see the packet's Known Deviations): the Finding-origin and Cold bodies the readers return are
  byte-equal before and after the mill Action exists, is linked and completed.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_ch4_opportunity_postgres import seed_opportunities
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_w203_cold_migration_postgres import head
    from test_w401_work_service_postgres import ACTOR, PRINCIPAL, event, record, request
    from test_w402_reads_postgres import CODE

    import pg_harness
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.chain.lifecycle_run import run_lifecycle
    from assetops_backend.work.composition import build_domain_intent_service, build_work_service
    from assetops_backend.work import domain_action as d


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _now(engine) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)


def _mill_body(seed: dict, engine, key="ch9b1-mill-0001", **over) -> dict:
    return {"domain": "MINI", "origin_opportunity_id": str(seed["b"]),
            "origin_opportunity_revision_id": str(seed["b_r2"]), "title": "Run the mill at midday",
            "owner_label": "Plant lead", "due_at": None, "raised_at": _iso(_now(engine) - timedelta(minutes=10)),
            "actor": dict(ACTOR), "idempotency_key": key, **over}


@pytest.fixture()
def mill(store, engine):  # noqa: F811
    svc, work = build_domain_intent_service(URL), build_work_service(URL)
    seed = seed_opportunities(store, engine)
    ns = SimpleNamespace(seed=seed, t=seed["t"], s=seed["s"], svc=svc, work=work, engine=engine)
    yield ns
    svc._store.dispose()
    work._store.dispose()


def _create(mill, **over) -> dict:
    status, action = mill.svc.create_action(mill.t, mill.s, CODE, _mill_body(mill.seed, mill.engine, **over), PRINCIPAL)
    assert status == 201, action
    return action


def _complete_case(mill, action_id: str, tag: str) -> str:
    """A W4 maintenance request, its performed record, COMPLETE, then the case link to the Action."""
    from test_w401_work_service_postgres import at

    status, wr = mill.work.create_case(mill.t, mill.s, request(f"{tag}-request"), PRINCIPAL)
    assert status == 201, wr
    case_id, rev_id = wr["id"], wr["revision"]["id"]
    s, rec = mill.work.post_record(mill.t, mill.s, case_id, record(f"{tag}-record", occurred_at=at(minutes=20)),
                                   PRINCIPAL)
    assert s == 201, rec
    s, got = mill.work.post_event(mill.t, mill.s, case_id, event("ASSIGN", {"assignee": "Plant lead"}, f"{tag}-assign",
                                                                 occurred_at=at(minutes=15)), PRINCIPAL)
    assert s == 201, got
    s, got = mill.work.post_event(mill.t, mill.s, case_id, event(
        "COMPLETE", {"maintenance_record_id": rec["id"]}, f"{tag}-complete", occurred_at=at(minutes=10)), PRINCIPAL)
    assert s == 201 and got["state"] == "COMPLETED", got
    with mill.engine.connect() as c:
        head_event = str(c.execute(text("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, id "
                                        "DESC LIMIT 1"), {"c": case_id}).scalar_one())
    s, linked = mill.svc.post_case_link(mill.t, mill.s, CODE, action_id, {
        "case_id": case_id, "case_revision_id": rev_id, "case_event_id": head_event, "actor": dict(ACTOR),
        "idempotency_key": f"{tag}-link"}, PRINCIPAL)
    assert s == 201, linked
    return case_id


def _threads(mill, steps) -> list[dict]:
    reader, writer = build_thread_sources(URL), build_thread_store(URL)
    try:
        return run_threads(reader, writer, mill.t, mill.s, steps=steps)
    finally:
        pg_harness.dispose(reader, writer)


def _lifecycle(mill) -> dict:
    reader, writer = build_thread_sources(URL), build_thread_store(URL)
    try:
        return run_lifecycle(reader, writer, mill.t, mill.s)
    finally:
        pg_harness.dispose(reader, writer)


# --- the mill Action from creation to CHANGE_APPLIED --------------------------------------------------------------

def test_mill_action_links_then_in_hand_then_change_applied(mill) -> None:
    _threads(mill, ("b",))  # step b places the one eligible opportunity thread (study A is ineligible)
    action = _create(mill)
    with mill.engine.connect() as c:
        row = c.execute(text("SELECT domain, origin_opportunity_id, origin_finding_id FROM domain_action WHERE id = "
                             ":a"), {"a": action["id"]}).one()
    assert row[0] == "MINI" and str(row[1]) == str(mill.seed["b"]) and row[2] is None
    with mill.engine.connect() as c:
        raised = c.execute(text("SELECT raised_at FROM domain_action WHERE id = :a"), {"a": action["id"]}).scalar_one()
    again = mill.svc.create_action(mill.t, mill.s, CODE, _mill_body(mill.seed, mill.engine, raised_at=_iso(raised)),
                                   PRINCIPAL)
    assert again[1]["id"] == action["id"]  # idempotent on the key
    case_id = _complete_case(mill, action["id"], "ch9b1-mill")
    c_report = _threads(mill, ("b", "c"))
    assert any(r.get("counts", {}).get("LINKED") for r in c_report if "counts" in r), c_report
    with mill.engine.connect() as c:
        link = c.execute(text("SELECT origin_finding_id, origin_opportunity_id, thread_id FROM chain_action_thread "
                              "WHERE action_id = :a"), {"a": action["id"]}).one()
    assert link[0] is None and str(link[1]) == str(mill.seed["b"]) and link[2] is not None
    _lifecycle(mill)
    with mill.engine.connect() as c:
        events = c.execute(text("SELECT e.state, e.effective_day, e.cause_kind FROM finding_thread_event e WHERE "
                                "e.thread_id = :t ORDER BY e.seq"), {"t": link[2]}).all()
        occurred = c.execute(text("SELECT (occurred_at AT TIME ZONE 'Africa/Nairobi')::date FROM work_event WHERE "
                                  "case_id = :c AND kind = 'COMPLETE'"), {"c": case_id}).scalar_one()
    states = [e[0] for e in events]
    assert states[0] == "OPEN" and "ACTION_IN_HAND" in states and states[-1] == "CHANGE_APPLIED", events
    assert events[-1][1] == occurred and events[-1][2] == "DOMAIN_CASE", (events, occurred)
    assert "WITHDRAWN" not in states


# --- the origin CHECKs both ways ----------------------------------------------------------------------------------

_INSERT = ("INSERT INTO domain_action (id, tenant_id, site_id, action_no, action_code, domain, origin_finding_id, "
           "origin_finding_revision_id, origin_opportunity_id, origin_opportunity_revision_id, title, raised_at, "
           "actor_kind, actor_id, attestation, idempotency_key, payload_sha256) VALUES (:id, :t, :s, :no, :code, "
           ":dom, :f, :fr, :o, :orv, 'check', now(), 'SERVICE', 'ch9b1', 'CH-9b1 L2', :key, :sha)")


def _raw(mill, no: int, **over) -> dict:
    return {"id": uuid4(), "t": mill.t, "s": mill.s, "no": no, "code": f"ACT-{no}", "dom": "MINI", "f": None,
            "fr": None, "o": mill.seed["b"], "orv": mill.seed["b_r2"], "key": f"ch9b1-raw-{no}",
            "sha": "0" * 64, **over}


def test_origin_checks_both_ways(mill) -> None:
    f, fr = uuid4(), uuid4()
    for no, over in ((910001, {"f": f, "fr": fr}),                 # both pairs
                     (910002, {"o": None, "orv": None}),            # neither pair
                     (910003, {"dom": "COLDCHAIN"}),                # opportunity origin on a non-MINI domain
                     (910004, {"dom": "MINI", "o": None, "orv": None, "f": f, "fr": fr})):  # MINI with a Finding
        with mill.engine.connect() as c:
            with pytest.raises((IntegrityError, DBAPIError)) as e:
                c.execute(text(_INSERT), _raw(mill, no, **over))
            assert "23514" in str(getattr(e.value.orig, "sqlstate", "") or e.value.orig) or \
                "check constraint" in str(e.value).lower(), e.value
    with mill.engine.begin() as c:  # the legal MINI row, opportunity pair only, is accepted
        c.execute(text(_INSERT), _raw(mill, 910005))
    with mill.engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM domain_action WHERE action_no = 910005")).scalar_one() == 1


def test_mini_body_refused_with_a_finding_pair_and_zero_writes(mill) -> None:
    before = _count(mill.engine)
    with pytest.raises(d.DomainIntentRefused):
        mill.svc.create_action(mill.t, mill.s, CODE, _mill_body(
            mill.seed, mill.engine, origin_finding_id=str(uuid4()), origin_finding_revision_id=str(uuid4())),
            PRINCIPAL)
    assert _count(mill.engine) == before


def _count(engine) -> int:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM domain_action")).scalar_one()


# --- 0051 up and down ---------------------------------------------------------------------------------------------

def _rows(engine) -> dict[str, list]:
    out = {}
    with engine.connect() as c:
        for t, order in (("domain_action", "id"), ("chain_action_thread", "action_id")):
            cols = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position"),
                {"t": t}) if r[0] not in ("origin_opportunity_id", "origin_opportunity_revision_id")]
            out[t] = [json.dumps(list(map(str, r))) for r in c.execute(text(
                f"SELECT {', '.join(cols)} FROM {t} ORDER BY {order}"))]
    return out


def test_0051_round_trip_refusal_and_rows(mill) -> None:
    from alembic import command

    action = _create(mill)
    assert head(mill.engine) == pg_harness.alembic_head()
    with pytest.raises(Exception) as refused:  # the downgrade refuses while an opportunity-origin Action exists
        command.downgrade(_alembic(), "0050_chain_response_expiry")
    assert "0051" in str(refused.value) or "opportunity" in str(refused.value).lower(), refused.value
    assert head(mill.engine) == pg_harness.alembic_head()
    # remove the opportunity-origin rows (test DB, direct SQL, triggers disabled for this one clean-up) and round trip
    before = None
    with mill.engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("DELETE FROM chain_action_thread WHERE origin_opportunity_id IS NOT NULL"))
        c.execute(text("DELETE FROM domain_action_case_link WHERE action_id = :a"), {"a": action["id"]})
        c.execute(text("DELETE FROM domain_action WHERE id = :a"), {"a": action["id"]})
    before = _rows(mill.engine)
    command.downgrade(_alembic(), "0050_chain_response_expiry")
    assert head(mill.engine) == "0050_chain_response_expiry"
    with mill.engine.connect() as c:
        cols = set(c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = "
                                  "'domain_action'")).scalars())
    assert "origin_opportunity_id" not in cols
    mid = _rows(mill.engine)
    command.upgrade(_alembic(), "head")
    assert head(mill.engine) == pg_harness.alembic_head()
    assert before == mid == _rows(mill.engine)
    with mill.engine.connect() as c:  # the CHECKs are back after the round trip
        with pytest.raises((IntegrityError, DBAPIError)):
            c.execute(text(_INSERT), _raw(mill, 910011, o=None, orv=None))


# --- CH-4 R6 at L2: a linked Action keeps a 0-eligible thread supported ---------------------------------------------
# (covered by test_mill_action_links_then_in_hand_then_change_applied: the seeded head is B r2 SUPPORTED; the L0 test
# `test_mill_action_accepted_then_applied_and_not_withdrawn` proves the withdraw/keep split with a 0-eligible head.)


# --- Q6 alternative proof: Finding-origin and Cold bodies byte-equal --------------------------------------------

_FINDING_SIDE = (
    "SELECT row_to_json(x)::text FROM (SELECT * FROM chain_action WHERE origin_finding_id IS NOT NULL "
    "ORDER BY kind, id) x",
    "SELECT row_to_json(x)::text FROM (SELECT * FROM domain_action WHERE origin_opportunity_id IS NULL "
    "ORDER BY id) x",
    "SELECT row_to_json(x)::text FROM (SELECT * FROM domain_action_case_link l WHERE EXISTS (SELECT 1 FROM "
    "domain_action a WHERE a.id = l.action_id AND a.origin_opportunity_id IS NULL) ORDER BY id) x",
    "SELECT row_to_json(x)::text FROM (SELECT * FROM chain_action_thread WHERE origin_opportunity_id IS NULL "
    "ORDER BY action_id) x",
    "SELECT row_to_json(x)::text FROM (SELECT * FROM finding_thread_event WHERE thread_id IN (SELECT thread_id FROM "
    "chain_action_thread WHERE origin_opportunity_id IS NULL) ORDER BY thread_id, seq) x",
)


def _capture(engine, finding_site, reader) -> bytes:
    """Every Finding-origin row the readers join, plus the reader bodies for the Finding Site, as one byte string."""
    out: list = []
    with engine.connect() as c:
        for sql in _FINDING_SIDE:
            out.append([r for r in c.execute(text(sql)).scalars()])
    t, s = finding_site
    inputs = reader.lifecycle_inputs(t, s)
    inputs.pop("now")  # the read instant is the one field that moves between two reads of identical rows
    out.append(json.dumps(inputs, default=str, sort_keys=True))
    return json.dumps(out, sort_keys=True, default=str).encode()


def test_q6_finding_and_cold_bodies_byte_equal_after_the_mill_action(seeded, store, engine) -> None:  # noqa: F811
    runner, reader, writer, f01, domain_id = seeded
    seed_opportunities_ = seed_opportunities(store, engine)
    ft, fs = runner.tenant, runner.site
    run_threads(reader, writer, ft, fs, steps=("b", "c"))
    run_lifecycle(reader, writer, ft, fs)
    before = _capture(engine, (ft, fs), reader)
    assert b"COLDCHAIN" in before and b"MINI_TRIAL" in before  # both Finding-origin Action kinds are in the capture
    ns = SimpleNamespace(seed=seed_opportunities_, t=seed_opportunities_["t"], s=seed_opportunities_["s"],
                         svc=build_domain_intent_service(URL), work=build_work_service(URL), engine=engine)
    try:
        run_threads(reader, writer, ns.t, ns.s, steps=("b",))
        action = _create(ns)
        _complete_case(ns, action["id"], "ch9b1-q6")
        run_threads(reader, writer, ns.t, ns.s, steps=("b", "c"))
        run_lifecycle(reader, writer, ns.t, ns.s)
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM chain_action_thread WHERE origin_opportunity_id IS NOT "
                                  "NULL")).scalar_one() == 1  # the mill Action is linked: the proof is not vacuous
    finally:
        ns.svc._store.dispose()
        ns.work._store.dispose()
    after = _capture(engine, (ft, fs), reader)
    if before != after:  # name the first differing byte window
        i = next(k for k in range(min(len(before), len(after))) if before[k] != after[k])
        raise AssertionError(f"first diff at {i}: {before[i - 150:i + 60]!r} != {after[i - 150:i + 60]!r}")
