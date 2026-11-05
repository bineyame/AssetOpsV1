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
    status, action = mill.svc.create_action(mill.t, mill.s, getattr(mill, "code", CODE), _mill_body(mill.seed, mill.engine, **over), PRINCIPAL)
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
    s, linked = mill.svc.post_case_link(mill.t, mill.s, getattr(mill, "code", CODE), action_id, {
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
    assert "WITHDRAWN" not in states  # vacuous here (head is SUPPORTED); the L0 test carries the R6 split


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
# Not provable at L2 without redesigning the CH-4 seed: the seeded head is B r2 SUPPORTED, so "no WITHDRAWN" holds with
# or without the link. The non-vacuous split (a 0-eligible head withdrawn without the link, kept with it) is the L0
# test `test_mill_action_accepted_then_applied_and_not_withdrawn`; this file relies on it (review L1).


# --- Q6 alternative proof: the served Finding-origin and Cold bodies, byte-equal -----------------------------------
# One tenant and one Site (the S4 Kobo Site): its Finding-origin threads and Actions and the seeded Cold Action are
# served, the mill Action is then added to that SAME Site, linked and completed, and the same routes are served again.

FINDING_SITE = "KOBO-001"
_CLOCK = {"known_at", "read_at", "generated_at", "now"}  # wall-clock read instants only (the default known_at is the read time)


def _mask(node):
    if isinstance(node, dict):
        return {k: ("<clock>" if k in _CLOCK else _mask(v)) for k, v in node.items()}
    return [_mask(v) for v in node] if isinstance(node, list) else node


def _is_finding_origin(row) -> bool:
    return isinstance(row, dict) and "opportunity" not in json.dumps(row, default=str).lower()


def _bodies(app, engine, domain_id, plant=None) -> dict:
    """The served bodies, each as (status, masked JSON): board, Site chain, thread route, Actions list, the MINI_TRIAL
    verification body and the Cold domain-work index and action. `plant` is the mutation hook of the non-vacuity run."""
    with engine.connect() as c:
        thread, action = c.execute(text(
            "SELECT CAST(t.thread_id AS text), CAST(t.action_id AS text) FROM chain_action_thread t JOIN chain_action a "
            "ON a.id = t.action_id WHERE t.origin_finding_id IS NOT NULL AND a.kind = 'MINI_TRIAL' "
            "ORDER BY t.action_id LIMIT 1")).one()
        day = c.execute(text("SELECT (episode_start AT TIME ZONE 'Africa/Nairobi')::date FROM "
                             "finding_thread_occurrence WHERE finding_id IS NOT NULL ORDER BY thread_id LIMIT 1")
                        ).scalar_one()
    window = {"from": "2026-09-01T00:00:00Z", "to": "2026-12-31T00:00:00Z"}
    routes = {"board": (f"/api/sites/{FINDING_SITE}/outcome-board", {"date": str(day)}),
              "chain": (f"/api/sites/{FINDING_SITE}/chain", {"date": str(day)}),
              "thread": (f"/api/sites/{FINDING_SITE}/threads/{thread}", {}),
              "actions": (f"/api/sites/{FINDING_SITE}/action-index", window),
              "verification": (f"/api/sites/{FINDING_SITE}/actions/{action}/verification/outcome", {}),
              "cold_index": (f"/api/sites/{FINDING_SITE}/domain-work/action-index", window),
              "cold_action": (f"/api/sites/{FINDING_SITE}/domain-work/actions/{domain_id}", {})}
    out = {}
    for name, (path, params) in routes.items():
        r = app.get(path, params=params)
        out[name] = (r.status_code, _mask(r.json()))
    if plant:
        plant(out)
    return out


def _finding_view(bodies: dict) -> dict:
    """What must not move: every body whole, except the Site-wide lists (chain threads and actions, Actions-list rows),
    where only the Finding-origin entries are kept (the mill thread and Action legitimately join those lists)."""
    view = dict(bodies)
    for name, key in (("chain", "threads"), ("chain", "actions"), ("actions", "rows")):
        status, body = bodies[name]
        if isinstance(body, dict) and isinstance(body.get(key), list):
            kept = {**body, key: [r for r in body[key] if _is_finding_origin(r)]}
            for extra in ("total_count", "counts", "outcomes"):
                kept.pop(extra, None)
            view[name] = (status, kept)
    return view


def _q6(seeded, store, engine, monkeypatch, plant=None):  # noqa: F811
    from fastapi.testclient import TestClient

    from assetops_backend.config import load_feature_flags
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.main import create_app
    from test_w402_reads_postgres import enable

    runner, reader, writer, f01, domain_id = seeded
    ft, fs = runner.tenant, runner.site
    run_threads(reader, writer, ft, fs, steps=("a", "b", "c", "d"))
    run_lifecycle(reader, writer, ft, fs)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "0" * 64)
    with TestClient(create_app(load_feature_flags())) as app:
        enable(engine, fs)
        seed = seed_opportunities(store, engine, site=(ft, fs))  # the studies sit on the Finding Site itself
        before = _bodies(app, engine, domain_id)
        assert before["thread"][0] == 200 and before["chain"][0] == 200, before["thread"]  # non-empty finding side
        assert before["board"][0] == 200 and before["verification"][0] == 200, (before["board"], before["verification"])
        ns = SimpleNamespace(seed=seed, t=ft, s=fs, svc=build_domain_intent_service(URL), work=build_work_service(URL),
                             engine=engine, code=FINDING_SITE)
        try:
            run_threads(reader, writer, ft, fs, steps=("b",))
            action = _create(ns)
            _complete_case(ns, action["id"], "ch9b1-q6")
            run_threads(reader, writer, ft, fs, steps=("b", "c"))
            run_lifecycle(reader, writer, ft, fs)
            with engine.connect() as c:  # the mill Action is on this Site and linked: the proof is not vacuous
                assert c.execute(text("SELECT count(*) FROM chain_action_thread WHERE origin_opportunity_id IS NOT "
                                      "NULL AND site_id = :s"), {"s": fs}).scalar_one() == 1
            after = _bodies(app, engine, domain_id, plant)
        finally:
            ns.svc._store.dispose()
            ns.work._store.dispose()
    return _finding_view(before), _finding_view(after)


def test_q6_finding_and_cold_bodies_byte_equal_after_the_mill_action(seeded, store, engine, monkeypatch) -> None:  # noqa: F811
    before, after = _q6(seeded, store, engine, monkeypatch)
    for name in before:
        assert json.dumps(before[name], sort_keys=True) == json.dumps(after[name], sort_keys=True), name


def test_q6_proof_can_fail_a_planted_key_in_a_finding_body(seeded, store, engine, monkeypatch) -> None:  # noqa: F811
    """Non-vacuity: a key leaking into the Finding-origin thread body after the mill Action fails the comparison."""
    def plant(out):
        status, body = out["thread"]
        out["thread"] = (status, {**body, "origin_opportunity_id": "leak"})
    before, after = _q6(seeded, store, engine, monkeypatch, plant)
    assert json.dumps(before["thread"], sort_keys=True) != json.dumps(after["thread"], sort_keys=True)
