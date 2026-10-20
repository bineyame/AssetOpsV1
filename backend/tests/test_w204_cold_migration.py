"""W2-04 commit 1: migration `0023_w2_cold_consequence` against Postgres.

`.agent/W2-04-build-spec.md` "Money schema `0023` and rules": upgrade over existing mini-grid money keeps its rows,
constraints, triggers and reads byte-stable; the four cold consequence tables are tenant/Site scoped, append-only and
unpriced by CHECK; dirty work is trigger-only (cold FindingRevision, cold episode revision, source-gate link) with
the canonical dirty key; existing cold heads are backfilled once, idempotently; and downgrade refuses while any
W2-04 row exists, deleting nothing. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from datetime import timedelta
from uuid import uuid4

import pytest

from assetops_backend.financials.cold_consequence import selected_instant

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import BACKEND, _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import POWER_DAY, _release_connections, site  # noqa: F401
    from test_w203_cold_migration_postgres import (
        T0, Ctx, _replica, _sha, constraint, head, insert_cold_finding, insert_episode, insert_link, insert_revision,
        scalar, table_exists)

    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker

HEAD = "0026_w2_ev_money"  # W2-07: 0026 sits above 0025
PREVIOUS = "0022_w2_cold_assessment"
REFUSED = "Downgrade of 0023_w2_cold_consequence refused"
TABLES = ("cold_consequence_revision", "cold_consequence_evidence", "cold_consequence_work",
          "cold_consequence_work_attempt")
LOCK = "PERFORM pg_advisory_xact_lock(hashtextextended('cold_consequence_enqueue:' || p_site_id::text, 0));"


def _migration():
    path = BACKEND / "migrations" / "versions" / "0023_w2_cold_consequence.py"
    spec = importlib.util.spec_from_file_location("m0023", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Q3: UTC `Z`, whole seconds, or six fractional digits when microseconds are nonzero (never truncated); the one
# Python spelling lives in the pure derivation module and the golden vectors below pin SQL against it.
_z = selected_instant


def dirty_key(cause, locator, t, s, start, end, room) -> str:
    """The canonical dirty key the triggers must store: SHA-256 of canonical JSON (sorted, no whitespace)."""
    doc = [cause, str(locator), str(t), str(s), _z(start), _z(end), str(room)]
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def rows(engine, table, where="TRUE", **params) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(f"SELECT * FROM {table} WHERE {where}"), params)]


def work(engine, ctx) -> list[dict]:  # noqa: F811
    return sorted(rows(engine, "cold_consequence_work", "site_id = :s", s=ctx.s), key=lambda w: str(w["id"]))


def remove_all_cold(engine) -> None:  # noqa: F811
    _replica(engine, *(f"DELETE FROM {t}" for t in reversed(TABLES)),
             "DELETE FROM cold_episode_evidence", "DELETE FROM cold_episode_revision", "DELETE FROM cold_episode",
             "DELETE FROM finding_revision_evidence WHERE finding_revision_id IN "
             "(SELECT id FROM finding_revision WHERE domain = 'cold_chain')",
             "DELETE FROM finding_revision WHERE domain = 'cold_chain'",
             "DELETE FROM finding WHERE domain = 'cold_chain'")


def assessment_window(engine, ctx):  # noqa: F811
    with engine.connect() as c:
        return tuple(c.execute(text("SELECT window_start, window_end FROM assessment_revision WHERE id = :a"),
                               {"a": ctx.assessment}).one())


def finding_revision_id(engine, finding_id):  # noqa: F811
    return scalar(engine, "SELECT id FROM finding_revision WHERE finding_id = :f ORDER BY revision_no DESC LIMIT 1",
                  f=finding_id)


def money_snapshot(engine) -> dict:  # noqa: F811
    """Every mini-grid money row (as canonical JSON text), constraint and trigger definition."""
    with engine.connect() as c:
        tables = [r[0] for r in c.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'financial_%' "
            "ORDER BY tablename"))]
        data = {t: sorted(r[0] for r in c.execute(text(f"SELECT row_to_json(x)::text FROM {t} x"))) for t in tables}
        cons = sorted(tuple(r) for r in c.execute(text(
            "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid::regclass::text LIKE 'financial_%'")))
        trig = sorted(tuple(r) for r in c.execute(text(
            "SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger WHERE NOT tgisinternal "
            "AND tgname LIKE 'financial_%'")))
        procs = sorted(tuple(r) for r in c.execute(text(
            "SELECT proname, prosrc FROM pg_proc WHERE proname LIKE 'financial_%'")))
    return {"data": data, "constraints": cons, "triggers": trig, "functions": procs}


# W2-07: a downgrade below 0026 restores the 0010 diesel-only key/unit CHECKs and drops the EV-only positive CHECK;
# every other mini-grid money row, constraint, trigger and function is unchanged.
_DIESEL_ONLY = {
    "financial_assumption_revision_assumption_key_check": "CHECK ((assumption_key = 'diesel_price_per_litre'::text))",
    "financial_assumption_revision_unit_check": "CHECK ((unit = 'currency/L'::text))",
}


def below_0026(snapshot: dict) -> dict:
    cons = sorted((t, n, _DIESEL_ONLY.get(n, d)) for t, n, d in snapshot["constraints"]
                  if n != "financial_assumption_revision_ev_positive")
    return {**snapshot, "constraints": cons}


def insert_consequence(engine, ctx, frev, erev, **over):  # noqa: F811
    cid = uuid4()
    start, end = assessment_window(engine, ctx)
    cols = {"id": cid, "t": ctx.t, "s": ctx.s, "f": frev, "e": erev, "a": ctx.assessment, "n": 1, "prior": None,
            "kind": "PRODUCT_EXPOSURE", "state": "UNPRICED", "reason": "Unpriced product exposure", "ws": start,
            "we": end, "room": ctx.assets[0], "group": "cold:" + _sha("group"), "unit": "degC_min", "ql": "30",
            "qh": "60", "al": None, "ah": None, "cur": None, "fb": _sha("finding-basis"), "cb": _sha(f"cb:{cid}"),
            "model": "cold-exposure/1", "cls": "REGISTERED_SIMULATION", "gate": _sha("gate"), "ids": "[]",
            "lim": None}
    cols.update(over)
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO cold_consequence_revision (id, tenant_id, site_id, finding_revision_id, episode_revision_id, "
            "assessment_revision_id, revision_no, prior_revision_id, kind, state, reason, window_start, window_end, "
            "room_asset_id, overlap_group, quantity_unit, quantity_low, quantity_high, amount_low, amount_high, "
            "currency, finding_basis_sha256, consequence_basis_sha256, model_id, source_classification, "
            "source_gate_sha256, assumption_revision_ids, limitation) VALUES (:id, :t, :s, :f, :e, :a, :n, :prior, "
            ":kind, :state, :reason, :ws, :we, :room, :group, :unit, :ql, :qh, :al, :ah, :cur, :fb, :cb, :model, "
            ":cls, :gate, CAST(:ids AS jsonb), :lim)"), cols)
    return cols["id"]


def cold_heads(engine, ctx):  # noqa: F811
    """One cold episode revision with a SUPPORT link and one cold FindingRevision on the mini-grid Site."""
    episode = insert_episode(engine, ctx)
    erev = insert_revision(engine, ctx, episode)
    insert_link(engine, ctx, erev, ctx.evidence[0])
    finding = insert_cold_finding(engine, ctx)
    return erev, finding_revision_id(engine, finding)


@pytest.fixture()
def ctx(site, engine):  # noqa: F811
    c = Ctx(site, engine)
    remove_all_cold(engine)
    yield c
    remove_all_cold(engine)


class TestMigration0023:
    def test_upgrade_preserves_minigrid_money_and_downgrade_drops_only_w204(self, site, ctx, engine) -> None:  # noqa: F811
        from alembic import command

        site.publish("v1")
        worker = ConsequenceRecomputeWorker(site.store, site.prices, CONSEQUENCE_UNAVAILABLE)
        assert all(o.succeeded for o in worker.run_pending(site.tenant, site.site))
        rev = site.on(POWER_DAY)

        def read():
            return site.store.load_input(site.tenant, site.site, rev["finding_id"], rev["id"])

        before, before_read = money_snapshot(engine), read()
        assert before["data"]["financial_consequence_revision"] and before["data"]["financial_consequence_work"]
        assert head(engine) == HEAD
        config = _alembic()
        site.store.dispose()
        site.prices.dispose()
        engine.dispose()
        try:
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS
            assert not any(table_exists(engine, t) for t in TABLES)
            assert constraint(engine, "batch_publication_link_scope_unique") is None
            assert scalar(engine, "SELECT count(*) FROM pg_proc WHERE proname LIKE 'cold_consequence%'") == 0
            assert scalar(engine, "SELECT count(*) FROM pg_trigger WHERE tgname LIKE 'cold_consequence%'") == 0
            assert money_snapshot(engine) == below_0026(before)
            command.upgrade(config, "head")
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        assert head(engine) == HEAD and all(table_exists(engine, t) for t in TABLES)
        assert money_snapshot(engine) == before and read() == before_read
        assert "UNIQUE (tenant_id, site_id, batch_id)" in constraint(engine, "batch_publication_link_scope_unique")

    def test_every_enqueue_path_takes_the_one_site_lock(self, engine) -> None:  # noqa: F811
        with engine.connect() as c:
            bodies = dict(c.execute(text(
                "SELECT proname, prosrc FROM pg_proc WHERE proname LIKE 'cold_consequence_dirty_on_%'")).all())
            enqueue = c.execute(text("SELECT prosrc FROM pg_proc WHERE proname = 'cold_consequence_enqueue'")
                                ).scalar_one()
        assert sorted(bodies) == ["cold_consequence_dirty_on_episode_revision",
                                  "cold_consequence_dirty_on_finding_revision", "cold_consequence_dirty_on_source_gate"]
        assert all(LOCK in b for b in bodies.values()) and _migration().ENQUEUE_LOCK == LOCK
        assert "ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING" in enqueue
        assert "ASSUMPTION" not in json.dumps(bodies) + enqueue


class TestScopeAppendOnlyAndUnpriced:
    def test_scoped_fks_checks_and_uniques(self, ctx, engine) -> None:  # noqa: F811
        erev, frev = cold_heads(engine, ctx)
        cid = insert_consequence(engine, ctx, frev, erev)
        refused = [
            ({"s": uuid4()}, IntegrityError),  # foreign Site: the Site and every scoped FK refuse
            ({"t": uuid4()}, IntegrityError),
            ({"f": uuid4()}, IntegrityError),
            ({"e": uuid4()}, IntegrityError),
            ({"a": uuid4()}, IntegrityError),
            ({"room": uuid4()}, IntegrityError),
            ({"al": "0"}, IntegrityError),  # no amount, not even zero
            ({"ah": "10"}, IntegrityError),
            ({"cur": "USD"}, IntegrityError),
            ({"unit": "none"}, IntegrityError),  # 'none' carries no quantity
            ({"ql": "-1"}, IntegrityError),
            ({"ql": "70", "qh": "60"}, IntegrityError),
            ({"qh": None}, IntegrityError),  # a null degC_min bound needs a limitation or WITHHELD
            ({"group": "cold-" + _sha("g")}, IntegrityError),
            ({"model": "cold-repair/1"}, IntegrityError),
            ({"kind": "RECORDED_REPAIR"}, IntegrityError),
            ({"reason": "  "}, IntegrityError),
            ({"ws": T0 + timedelta(hours=2), "we": T0 + timedelta(hours=2)}, IntegrityError),
            ({"ids": "{}"}, IntegrityError),
            ({"n": 2}, IntegrityError),  # revision 2 needs a prior
            ({"prior": cid}, IntegrityError),  # revision 1 has none
            ({"fb": "ABC"}, IntegrityError),
            ({"cls": "ATTESTED_REAL_SOURCE"}, IntegrityError),  # Q7: exactly the four S4-05 aggregate classes
            ({"cls": "simulated"}, IntegrityError),
        ]
        for over, error in refused:
            with pytest.raises(error):
                insert_consequence(engine, ctx, frev, erev, **over)
        # Allowed nulls: an open upper bound with a limitation, a withheld claim, a repair with no quantity.
        def other():
            return finding_revision_id(engine, insert_cold_finding(engine, ctx))

        insert_consequence(engine, ctx, other(), erev, qh=None, lim="Upper bound not observed")
        insert_consequence(engine, ctx, other(), erev, ql=None, qh=None, state="WITHHELD")
        insert_consequence(engine, ctx, frev, erev, kind="RECORDED_REPAIR", model="cold-repair/1", unit="none",
                           ql=None, qh=None, state="WITHHELD")
        # Basis and revision number are unique per (FindingRevision, kind); a chained revision 2 is accepted.
        same = rows(engine, "cold_consequence_revision", "id = :i", i=cid)[0]
        with pytest.raises(IntegrityError):
            insert_consequence(engine, ctx, frev, erev, cb=same["consequence_basis_sha256"])
        insert_consequence(engine, ctx, frev, erev, n=2, prior=cid, cb=_sha("second"))
        with pytest.raises(IntegrityError):
            insert_consequence(engine, ctx, frev, erev, n=2, prior=cid, cb=_sha("third"))
        assert rows(engine, "cold_consequence_revision", "id = :i", i=cid)[0]["created_at"] is not None

        def link(**kw):
            p = {"c": cid, "t": ctx.t, "s": ctx.s, "e": ctx.evidence[0], "u": "SUPPORT", **kw}
            with engine.begin() as c:
                c.execute(text("INSERT INTO cold_consequence_evidence (consequence_revision_id, tenant_id, site_id, "
                               "evidence_id, use, reason) VALUES (:c, :t, :s, :e, :u, NULL)"), p)

        link()
        link(u="CONTEXT")
        for kw in ({"s": uuid4()}, {"e": uuid4()}, {"u": "PRIVATE"}, {}):
            with pytest.raises(IntegrityError):
                link(**kw)

    def test_work_shape_attempt_shape_and_append_only(self, ctx, engine) -> None:  # noqa: F811
        erev, frev = cold_heads(engine, ctx)
        (w, *_) = [x for x in work(engine, ctx) if x["cause"] == "EPISODE_REVISION_APPENDED"]
        start, end = assessment_window(engine, ctx)
        # The cause shape: exactly the locator for its cause (a direct INSERT here is test-only).
        for cause, f, e, b in (("FINDING_REVISION_APPENDED", None, erev, None),
                               ("EPISODE_REVISION_APPENDED", frev, erev, None),
                               ("SOURCE_GATE_CHANGED", None, None, None)):
            with pytest.raises(IntegrityError), engine.begin() as c:
                c.execute(text(
                    "INSERT INTO cold_consequence_work (tenant_id, site_id, cause, finding_revision_id, "
                    "episode_revision_id, publication_batch_id, window_start, window_end, room_asset_id, "
                    "dirty_key_sha256) VALUES (:t, :s, :c, :f, :e, :b, :ws, :we, :r, :k)"),
                    ctx.p(c=cause, f=f, e=e, b=b, ws=start, we=end, r=ctx.assets[0], k=_sha(str(uuid4()))))

        def attempt(n, outcome, error, ids="[]", work_id=None, site_id=None):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO cold_consequence_work_attempt (tenant_id, site_id, work_id, attempt_no, outcome, "
                    "error_code, consequence_revision_ids) VALUES (:t, :s, :w, :n, :o, :err, CAST(:ids AS jsonb))"),
                    {"t": ctx.t, "s": site_id or ctx.s, "w": work_id or w["id"], "n": n, "o": outcome, "err": error,
                     "ids": ids})

        attempt(1, "FAILED", "COLD_BASIS_MISSING")
        attempt(2, "SUCCEEDED", None, json.dumps([str(uuid4())]))
        for args in ((3, "SUCCEEDED", "X"), (3, "FAILED", None), (3, "FAILED", "E", json.dumps([str(uuid4())])),
                     (2, "FAILED", "E"), (0, "FAILED", "E"), (3, "FAILED", "E", "[]", uuid4()),
                     (3, "FAILED", "E", "[]", None, uuid4())):
            with pytest.raises(IntegrityError):
                attempt(*args)
        cid = insert_consequence(engine, ctx, frev, erev)
        with engine.begin() as c:
            c.execute(text("INSERT INTO cold_consequence_evidence (consequence_revision_id, tenant_id, site_id, "
                           "evidence_id, use) VALUES (:c, :t, :s, :e, 'SUPPORT')"), ctx.p(c=cid, e=ctx.evidence[0]))
        for table in TABLES:
            for sql in (f"UPDATE {table} SET site_id = site_id", f"DELETE FROM {table}"):
                with pytest.raises(DBAPIError, match="append-only|immutable"), engine.begin() as c:
                    c.execute(text(sql))
        assert {t: scalar(engine, f"SELECT count(*) FROM {t}") > 0 for t in TABLES} == dict.fromkeys(TABLES, True)


class TestTriggerOnlyWork:
    def test_cold_revisions_enqueue_their_window_and_room_with_the_canonical_key(self, ctx, engine) -> None:  # noqa: F811
        start, end = assessment_window(engine, ctx)
        assert scalar(engine, "SELECT count(*) FROM cold_consequence_work") == 0  # mini-grid Findings enqueue none
        erev, frev = cold_heads(engine, ctx)
        got = {(w["cause"], w["episode_revision_id"] or w["finding_revision_id"]): w for w in work(engine, ctx)}
        assert set(got) == {("EPISODE_REVISION_APPENDED", erev), ("FINDING_REVISION_APPENDED", frev)}
        for (cause, locator), w in got.items():
            assert (w["window_start"], w["window_end"], w["room_asset_id"]) == (start, end, ctx.assets[0])
            assert w["dirty_key_sha256"] == dirty_key(cause, locator, ctx.t, ctx.s, start, end, ctx.assets[0])
            assert w["publication_batch_id"] is None and w["enqueued_at"] is not None
        # A repeat of the same key is a no-op; a mini-grid FindingRevision enqueues no cold work.
        with engine.begin() as c:
            c.execute(text("SELECT cold_consequence_enqueue('EPISODE_REVISION_APPENDED', :e, :t, :s, :ws, :we, :r)"),
                      ctx.p(e=erev, ws=start, we=end, r=ctx.assets[0]))
        assert len(work(engine, ctx)) == 2
        mini = scalar(engine, "SELECT id FROM finding_revision WHERE domain = 'mini_grid' AND site_id = :s LIMIT 1",
                      s=ctx.s)
        assert mini is not None
        assert not [w for w in work(engine, ctx) if w["finding_revision_id"] == mini]

    def test_sql_and_python_dirty_keys_match_for_whole_second_and_fractional_windows(self, ctx, engine) -> None:  # noqa: F811
        """Q3 golden vectors: SQL `cold_consequence_instant`/`cold_consequence_dirty_key` equal the Python spelling."""
        vectors = [(T0, T0 + timedelta(minutes=65), "2026-10-06T19:00:00Z", "2026-10-06T20:05:00Z"),
                   (T0 + timedelta(microseconds=1), T0 + timedelta(minutes=5, microseconds=250000),
                    "2026-10-06T19:00:00.000001Z", "2026-10-06T19:05:00.250000Z")]
        locator, room = uuid4(), ctx.room
        with engine.connect() as c:
            for start, end, start_text, end_text in vectors:
                assert (_z(start), _z(end)) == (start_text, end_text)
                got = c.execute(text("SELECT cold_consequence_instant(:a), cold_consequence_instant(:b), "
                                     "cold_consequence_dirty_key('FINDING_REVISION_APPENDED', :l, :t, :s, :a, :b, :r)"),
                                ctx.p(a=start, b=end, l=locator, r=room)).one()
                assert tuple(got) == (start_text, end_text, dirty_key("FINDING_REVISION_APPENDED", locator, ctx.t,
                                                                      ctx.s, start, end, room))
        assert vectors[0][2] != vectors[1][2]  # a fractional window is never truncated to the same key

    def test_excursion_and_start_response_share_the_chamber_room_never_the_generator(self, ctx, engine) -> None:  # noqa: F811
        """Q1: both episode kinds and both Finding kinds of one assessment enqueue the same window and chamber room;
        the START_RESPONSE generator (its episode asset and Finding subject) is never stored as the room."""
        generator = ctx.assets[1]
        assert generator != ctx.room
        excursion = insert_revision(engine, ctx, insert_episode(engine, ctx, key="exc"))
        start_episode = insert_episode(engine, ctx, key="start", asset=generator)
        with engine.begin() as c:
            c.execute(text("SET LOCAL session_replication_role = replica"))  # fixture helper inserts EXCURSION
            c.execute(text("UPDATE cold_episode SET kind = 'START_RESPONSE' WHERE id = :e"), {"e": start_episode})
        start_rev = insert_revision(engine, ctx, start_episode, basis="start")
        exc_finding = finding_revision_id(engine, insert_cold_finding(engine, ctx))
        start_finding = finding_revision_id(engine, insert_cold_finding(engine, ctx, subject=generator))
        start, end = assessment_window(engine, ctx)
        got = work(engine, ctx)
        assert {w["episode_revision_id"] or w["finding_revision_id"] for w in got} == {
            excursion, start_rev, exc_finding, start_finding}
        assert {(w["window_start"], w["window_end"], w["room_asset_id"]) for w in got} == {(start, end, ctx.room)}
        assert generator not in {w["room_asset_id"] for w in got}

    def test_unresolvable_room_raises_and_rolls_back_the_cold_append(self, ctx, engine) -> None:  # noqa: F811
        """Q8: an assessment whose Foundation basis names no chamber room refuses the cold revision append."""
        episode = insert_episode(engine, ctx)
        with pytest.raises(DBAPIError, match="chamber rooms in its Foundation basis"):
            insert_revision(engine, ctx, episode, assessment=ctx.mini_assessment)
        assert scalar(engine, "SELECT count(*) FROM cold_episode_revision WHERE episode_id = :e", e=episode) == 0
        assert work(engine, ctx) == []

    def test_source_gate_link_enqueues_only_heads_citing_that_batch(self, ctx, engine) -> None:  # noqa: F811
        erev, frev = cold_heads(engine, ctx)
        with engine.connect() as c:
            batch = c.execute(text(
                "SELECT b.* FROM ingestion_batch b JOIN accepted_evidence e ON e.batch_id = b.id "
                "WHERE e.id = :e"), {"e": ctx.evidence[0]}).mappings().one()
            linked = c.execute(text("SELECT count(*) FROM batch_publication_link WHERE batch_id = :b"),
                               {"b": batch["id"]}).scalar_one()
            other = c.execute(text(
                "SELECT b.* FROM ingestion_batch b WHERE b.site_id = :s AND b.id <> :b AND NOT EXISTS "
                "(SELECT 1 FROM batch_publication_link l WHERE l.batch_id = b.id) AND NOT EXISTS "
                "(SELECT 1 FROM cold_episode_evidence l JOIN accepted_evidence e ON e.id = l.evidence_id "
                "WHERE e.batch_id = b.id) LIMIT 1"), {"s": ctx.s, "b": batch["id"]}).mappings().first()
        assert linked == 0, "fixture batches carry no publication link yet"
        before = work(engine, ctx)

        def publish(b):
            pid = uuid4()
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO evidence_publication (id, tenant_id, site_id, gateway_id, source_id, "
                    "external_batch_id, payload_sha256, source_class, fixture_id, fixture_version, actor_kind, "
                    "actor_id, authorization_basis, channel, publication_trigger, recorded_at) VALUES (:p, :t, :s, "
                    ":g, :src, :x, :h, 'AUTHORED_DEMONSTRATION', 'w204', '1', 'SYSTEM', 'test', 'test', "
                    "'SYSTEM_FIXTURE', 'test', now())"),
                    {"p": pid, "t": b["tenant_id"], "s": b["site_id"], "g": b["gateway_id"], "src": b["source_id"],
                     "x": b["external_batch_id"], "h": b["payload_sha256"]})
                c.execute(text(
                    "INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, "
                    "source_id, external_batch_id, payload_sha256, linked_at) VALUES (:b, :p, :t, :s, :g, :src, "
                    ":x, :h, now())"),
                    {"b": b["id"], "p": pid, "t": b["tenant_id"], "s": b["site_id"], "g": b["gateway_id"],
                     "src": b["source_id"], "x": b["external_batch_id"], "h": b["payload_sha256"]})

        if other is not None:  # an unrelated batch's link dirties no cold basis
            publish(other)
            assert work(engine, ctx) == before
        publish(batch)
        start, end = assessment_window(engine, ctx)
        (gate,) = [w for w in work(engine, ctx) if w["cause"] == "SOURCE_GATE_CHANGED"]
        assert gate["publication_batch_id"] == batch["id"]
        assert (gate["finding_revision_id"], gate["episode_revision_id"]) == (None, None)
        assert gate["dirty_key_sha256"] == dirty_key("SOURCE_GATE_CHANGED", batch["id"], ctx.t, ctx.s, start, end,
                                                     ctx.assets[0])

    def test_backfill_enqueues_latest_heads_once(self, ctx, engine) -> None:  # noqa: F811
        from alembic import command

        episode = insert_episode(engine, ctx)
        old = insert_revision(engine, ctx, episode, n=1, basis="b1")
        new = insert_revision(engine, ctx, episode, n=2, basis="b2")
        finding = insert_cold_finding(engine, ctx)
        frev = finding_revision_id(engine, finding)
        _replica(engine, "DELETE FROM cold_consequence_work")
        config = _alembic()
        engine.dispose()
        try:
            command.downgrade(config, PREVIOUS)
            command.upgrade(config, "head")
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        got = sorted((w["cause"], str(w["episode_revision_id"] or w["finding_revision_id"])) for w in work(engine, ctx))
        assert got == sorted([("EPISODE_REVISION_APPENDED", str(new)), ("FINDING_REVISION_APPENDED", str(frev))])
        assert str(old) not in {g[1] for g in got}
        with engine.begin() as c:  # running the backfill again changes nothing
            for statement in _migration().BACKFILL.split(";"):
                if statement.strip():
                    c.execute(text(statement))
        assert sorted((w["cause"], str(w["episode_revision_id"] or w["finding_revision_id"]))
                      for w in work(engine, ctx)) == got


class TestDowngradeRefusal:
    def test_downgrade_refuses_while_any_w204_row_exists(self, ctx, engine) -> None:  # noqa: F811
        from alembic import command

        cold_heads(engine, ctx)
        counts = {t: scalar(engine, f"SELECT count(*) FROM {t}") for t in TABLES}
        assert counts["cold_consequence_work"] == 2
        config = _alembic()
        engine.dispose()
        try:
            with pytest.raises(DBAPIError, match=REFUSED):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD  # the whole downgrade rolled back
            assert {t: scalar(engine, f"SELECT count(*) FROM {t}") for t in TABLES} == counts  # nothing deleted
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
