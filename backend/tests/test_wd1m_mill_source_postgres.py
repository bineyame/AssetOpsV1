"""WD-1m L2 (FUEL-1 WD-1m-R §5, WD-1m-R2 §5): the mill verdict's example-data class, computed once when the verdict
is judged by `ActionStore.example_source_class`, equals a reference built from the S4-05 link reader, on real rows;
and it is stored in `details.source`, read by `_SITE_ACTIONS` and shown on the verdict-page wire.

The CH-2 `seeded` Finding Site (Africa/Nairobi, UTC+3) carries MINI_TRIAL Actions; the CH-9b mill Action is raised,
completed, linked, frozen and judged VERIFIED on that same Site (the CH-9b1 Q6 sequence). Each parity case then seeds
its own batches and evidence inside one transaction, calls the store method on that connection (the store's `_read`
is pointed at it), reads the reference there, and rolls back, so the cases share one verdict.

Reference (§5): the ids of `accepted_evidence` on the verdict's used days (Site-local) received by the outcome's
`recorded_at` -> `link_rows_on` -> `source_provenance.link_of` -> BOUND links with a class in `EXAMPLE_SOURCES` ->
`min`, else None.

Case 6 deviates in form only: Nairobi is UTC+3, so a Site-local reading that falls on another UTC day is one just
after local midnight (00:30 local on the first used day is 21:30 UTC the day before), not 23:30 local.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
import hashlib
from types import SimpleNamespace
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_ch9b1_opportunity_actions_postgres import FINDING_SITE, seed_opportunities
    from test_ch9b3_mill_verdict_postgres import _after, _close, _frozen, _later
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from zoneinfo import ZoneInfo

    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.chain.adapters.postgres_chain_read import _SITE_ACTIONS
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.lifecycle_run import run_lifecycle
    from assetops_backend.chain.vocabulary import EXAMPLE_SOURCES
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.evidence.source_provenance import BOUND, classify, link_of
    from assetops_backend.work.composition import build_domain_intent_service, build_work_service
    from test_w402_reads_postgres import enable

REG = "REGISTERED_SIMULATION"


def _sha(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def site_scope(c, t, s) -> dict:
    """The Site's existing gateway, source, foundation and binding revisions (the seeded rows' foreign keys)."""
    g, src = c.execute(text("SELECT gateway_id, id FROM source WHERE tenant_id = :t AND site_id = :s ORDER BY id LIMIT 1"),
                       {"t": t, "s": s}).one()
    one = lambda table: c.execute(text(f"SELECT id FROM {table} WHERE tenant_id = :t AND site_id = :s ORDER BY id "  # noqa: E731
                                       "LIMIT 1"), {"t": t, "s": s}).scalar_one()
    return {"t": t, "s": s, "g": g, "src": src, "fr": one("foundation_revision"),
            "bs": one("signal_binding_set_revision"), "br": one("signal_binding_revision")}


def seed_batch(c, scope: dict, at: list[tuple[datetime, datetime]], published: str | None) -> list[str]:
    """One batch with one MEASUREMENT row per `(source_time, received_at)`; `published` = a REGISTERED_SIMULATION
    publication and its link, None = unpublished (UNBOUND). Returns the evidence ids."""
    bid, ext = uuid4(), f"wd1m-{uuid4()}"
    sha = _sha(ext)
    received = min(r for _, r in at)
    p = {**scope, "b": bid, "ext": ext, "sha": sha, "recv": received}
    c.execute(text(
        "INSERT INTO ingestion_batch (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, "
        "schema_version, source_mode, foundation_revision_id, binding_set_revision_id, snapshot_sha256, batch_text, "
        "status, total_count, received_at) VALUES (:b, :t, :s, :g, :src, :ext, :sha, 1, 'SIMULATED', :fr, :bs, :sha, "
        "'{}', 'IN_PROGRESS', 1, :recv)"), p)
    ids = []
    for n, (source_time, received_at) in enumerate(at):
        eid = uuid4()
        ids.append(str(eid))
        c.execute(text(
            "INSERT INTO accepted_evidence (id, tenant_id, site_id, batch_id, ordinal, gateway_id, source_id, message_id, "
            "sequence_epoch, sequence, device_id, signal_id, role, family, source_time, published_at, received_at, "
            "quality, envelope_sha256, envelope_text, foundation_revision_id, binding_set_revision_id, "
            "binding_revision_id, configuration_outdated, source_mode, measurement, conversion_kind, original_unit, "
            "normalized_unit, original_value_text, normalized_value_text) VALUES (:e, :t, :s, :b, :n, :g, :src, :m, "
            "'wd1m', :n, 'wd1m-device', 'wd1m-signal', 'wd1m-role', 'MEASUREMENT', :st, :st, :rt, 'GOOD', :esha, '{}', "
            ":fr, :bs, :br, false, 'SIMULATED', 'MEAN', 'IDENTITY', 'kW', 'kW', '1', '1')"),
            {**p, "e": eid, "n": n, "m": f"{ext}-{n}", "st": source_time, "rt": received_at, "esha": _sha(eid)})
    if published:
        pid = uuid4()
        c.execute(text(
            "INSERT INTO evidence_publication (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, "
            "payload_sha256, source_class, actor_kind, actor_id, authorization_basis, channel, publication_trigger, "
            "recorded_at, run_id, run_identity_sha256) VALUES (:p, :t, :s, :g, :src, :ext, :sha, :cls, 'SYSTEM', "
            "'wd1m-test', 'WD-1m L2 seed', 'SYSTEM_LAB_RELEASE', 'wd1m', :recv, 'wd1m-run', :sha)"),
            {**p, "p": pid, "cls": published})
        c.execute(text(
            "INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, source_id, "
            "external_batch_id, payload_sha256, linked_at) VALUES (:b, :p, :t, :s, :g, :src, :ext, :sha, :recv)"),
            {**p, "p": pid})
    return ids


def reference(c, t, s, tz: str, days: list[str], recorded) -> str | None:
    """§5's reference: the used-day ids received by `recorded`, through the S4-05 link reader."""
    ids = list(c.execute(text(
        "SELECT CAST(id AS text) FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s "
        "AND CAST(source_time AT TIME ZONE :z AS date) = ANY(CAST(:d AS date[])) AND received_at <= :r"),
        {"t": t, "s": s, "z": tz, "d": days, "r": recorded}).scalars())
    links = [link_of(r) for r in link_rows_on(c, t, s, ids)] if ids else []
    found = [x.source_class for x in links if x.status == BOUND and x.source_class in EXAMPLE_SOURCES]
    return min(found) if found else None


def _local(day: str, tz: str, at: time) -> datetime:
    return datetime.combine(datetime.fromisoformat(day).date(), at, ZoneInfo(tz)).astimezone(timezone.utc)


@pytest.fixture()
def verdict(seeded, store, engine):  # noqa: F811
    """The mill judged VERIFIED on the `seeded` Finding Site (no published evidence yet: stored class None), which
    keeps its MINI_TRIAL Actions."""
    yield from _judged(seeded, store, engine, publish=False)


@pytest.fixture()
def published_verdict(seeded, store, engine):  # noqa: F811
    """The same, but a REGISTERED_SIMULATION batch is committed on every used day before the verdict is judged."""
    yield from _judged(seeded, store, engine, publish=True)


def _judged(seeded, store, engine, *, publish: bool):  # noqa: F811
    runner, reader, writer, _f01, _domain = seeded
    t, s = runner.tenant, runner.site
    run_threads(reader, writer, t, s, steps=("a", "b", "c", "d"))
    run_lifecycle(reader, writer, t, s)
    enable(engine, s)
    seed = seed_opportunities(store, engine, site=(t, s))
    mill = SimpleNamespace(seed=seed, t=t, s=s, svc=build_domain_intent_service(URL), work=build_work_service(URL),
                           engine=engine, code=FINDING_SITE)
    astore = PostgresActionStore(URL)  # the store `evaluate` writes through (the verdict service's own)
    try:
        run_threads(reader, writer, t, s, steps=("b",))
        svc, clock, aid, eff, tz = _frozen(mill, "wd1m")
        run_threads(reader, writer, t, s, steps=("b", "c"))
        _later(mill, eff, "11.5")
        clock.at = _after(eff, tz, 5)
        if publish:  # the used days of `_frozen` / `_later`: eff-1..3 and eff+1..3, read at Site-local noon
            noons = [_local((eff + timedelta(days=n)).isoformat(), tz, time(12)) for n in (-3, -2, -1, 1, 2, 3)]
            with engine.begin() as c:
                seed_batch(c, site_scope(c, t, s), [(n, n) for n in noons], REG)
        assert svc.evaluate_domain_plan(t, s, aid)["state"] == "VERIFIED"
        run_lifecycle(reader, writer, t, s)
        with engine.connect() as c:
            o = c.execute(text("SELECT details, recorded_at FROM verification_outcome WHERE domain_action_id = :a"),
                          {"a": aid}).one()
        days = list(o.details["baseline"]["days"]) + list(o.details["later"]["days"])
        yield SimpleNamespace(t=t, s=s, tz=tz, aid=aid, eff=eff.isoformat(), days=days, recorded=o.recorded_at,
                              engine=engine, astore=astore)
    finally:
        astore.dispose()
        _close(mill)
        mill.svc._store.dispose()
        mill.work._store.dispose()


def _case(v, seed) -> tuple[str | None, str | None]:
    """Seed inside one transaction, call the store method (its `_read` pointed at this connection) and the reference
    there, roll back. Returns (store method result, reference)."""
    with v.engine.connect() as c:
        tx = c.begin()
        v.astore._read = lambda work: work(c)  # instance attribute shadows the method for this call only
        try:
            seed(c, site_scope(c, v.t, v.s))
            got = v.astore.example_source_class(v.t, v.s, v.days, v.tz, v.recorded)
            return got, reference(c, v.t, v.s, v.tz, v.days, v.recorded)
        finally:
            del v.astore._read
            tx.rollback()


def test_the_mill_source_class_equals_the_link_reader_reference(verdict) -> None:
    v = verdict
    noon = lambda day: _local(day, v.tz, time(12))  # noqa: E731
    before = v.recorded - timedelta(hours=1)
    first, used = v.days[0], v.days[1]
    assert v.eff not in v.days and min(v.days) < v.eff < max(v.days)  # the effective day lies inside the range

    def check(n: int, seed, expected: str | None) -> None:
        got, ref = _case(v, seed)
        assert got == ref == expected, (n, got, ref, expected)

    # 1: used days only on the published batch.
    check(1, lambda c, sc: seed_batch(c, sc, [(noon(used), before)], REG), REG)

    # 2: used days only on the unpublished batch.
    check(2, lambda c, sc: seed_batch(c, sc, [(noon(used), before)], None), None)

    # 3: both; the mixed window keeps the label, where `classify` would not give a positive class.
    seen: dict = {}

    def both(c, sc):
        seen["ids"] = seed_batch(c, sc, [(noon(used), before)], REG) + seed_batch(c, sc, [(noon(first), before)], None)
        seen["state"] = classify(seen["ids"], {x.accepted_evidence_id: x for x in map(
            link_of, link_rows_on(c, v.t, v.s, seen["ids"]))})["state"]

    check(3, both, REG)
    assert seen["state"] not in EXAMPLE_SOURCES, ("case 3: classify", seen["state"])

    # 4: the published evidence lies on the effective day, inside the range but not used (proves the day filter).
    check(4, lambda c, sc: seed_batch(c, sc, [(noon(v.eff), before)], REG), None)

    # 5: the published evidence was received after the outcome's `recorded_at` (proves the knowledge limit).
    check(5, lambda c, sc: seed_batch(c, sc, [(noon(used), v.recorded + timedelta(minutes=1))], REG), None)

    # 6: 00:30 Site-local on the first used day, which is the day before in UTC, counts (proves the Site mapping).
    early = _local(first, v.tz, time(0, 30))
    assert early.date().isoformat() not in v.days
    check(6, lambda c, sc: seed_batch(c, sc, [(early, before)], REG), REG)

    # The empty window asks nothing of the database.
    assert v.astore.example_source_class(v.t, v.s, [], v.tz, v.recorded) is None


def _site_actions(c, v) -> dict:
    rows = [dict(r._mapping) for r in c.execute(_SITE_ACTIONS, {"t": v.t, "s": v.s})]
    return {r["action_id"]: r for r in rows}


def test_a_verdict_stored_without_a_source_reads_null_and_a_trial_keeps_its_own_path(verdict) -> None:
    """Case 7 (WD-1m-R2): the stored `details.source` is `{"source_class": None}` here (no published evidence at
    judging); with the key removed (a verdict stored before WD-1m) `_SITE_ACTIONS` reads NULL too; a MINI_TRIAL Action
    reads NULL (its class is not on this statement) and its row is unchanged by the verdict's source."""
    v = verdict
    with v.engine.connect() as c:
        tx = c.begin()
        try:
            stored = c.execute(text("SELECT details->'source' FROM verification_outcome WHERE domain_action_id = :a"),
                               {"a": v.aid}).scalar_one()
            assert stored == {"source_class": None}
            before = _site_actions(c, v)
            # the append-only trigger is lifted inside this rolled-back transaction only, to fake an old verdict row
            c.execute(text("ALTER TABLE verification_outcome DISABLE TRIGGER USER"))
            c.execute(text("UPDATE verification_outcome SET details = details - 'source' WHERE domain_action_id = :a"),
                      {"a": v.aid})
            after = _site_actions(c, v)
        finally:
            tx.rollback()
    assert before[v.aid]["source_class"] is None and after[v.aid]["source_class"] is None
    trials = {a: r for a, r in after.items() if r["kind"] == "MINI_TRIAL"}
    assert trials and all(r["source_class"] is None for r in trials.values())
    assert {a: r for a, r in before.items() if a != v.aid} == {a: r for a, r in after.items() if a != v.aid}


def test_judging_stores_the_class_the_board_statement_returns_and_the_verdict_page_shows(published_verdict) -> None:
    """End to end (WD-1m-R2): `MiddayShift.evaluate` over published-batch days stores `details.source`; `_SITE_ACTIONS`
    returns it; `summary_wire` shows it as `outcome.source_class`."""
    from assetops_backend.actions.verification_families import summary_wire

    v = published_verdict
    with v.engine.connect() as c:
        stored = c.execute(text("SELECT details->'source' FROM verification_outcome WHERE domain_action_id = :a"),
                           {"a": v.aid}).scalar_one()
        assert stored == {"source_class": REG}
        assert _site_actions(c, v)[v.aid]["source_class"] == REG
    ctx = v.astore.domain_plan_context(v.t, v.s, v.aid)
    wire = summary_wire({**ctx, "action": {**ctx["action"], "title": "x", "action_code": "ACT-9"}},
                        v.astore.domain_outcomes(v.t, v.s, v.aid), None)
    assert wire["outcome"]["source_class"] == REG
