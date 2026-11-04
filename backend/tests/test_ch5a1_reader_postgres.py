"""CH-5a1 L2 (build sheet Part A §A9 item 3): the ChainReader's SQL ports and the board route on Postgres.

Seeded as CH-2/CH-3 L2: the S4 Finding case runner (F01, F02 on one generator thread), a real ACCEPTED mini Action
through the s6 harness, then the `_settle_chain` path of `test_out_b4_board_postgres.py` (backfill steps a-d, then
the tick's `chain_threads` consume). `CaseRunner` cannot be cached in `setup_cache` (CH-2 packet deviation D-3), so the
module seeds once on `pg_harness.fresh_database()` (the `engine` fixture) and the tests run in file order: the
read-only checks first, then the ones that append (a snapshot revision, the F04 Finding, the APPLY).

Clocks: Finding revisions and their occurrences' `source_known_at` carry the runner's story clock (`runner.now`);
snapshot `computed_at` is the database clock. Each `known_at` cut is taken on the clock its rows carry.

"Later selection" is read as the snapshot store's latest-row selection (DISTINCT ON revision DESC): a later snapshot
revision of a (day, measure, subject) is not selected at an earlier `known_at`.

# TODO L2m (do not build until MD-0 merges; build sheet §A9 item 3, MD0-S2: Kobo only):
#   - every §A3 port over the full 14-day Kobo Site on `mechanism_db()`;
#   - `readiness_of` per MD-0 day equals the E1 MD-0 list;
#   - R8 around `late_fill(KOBO-001, D7)`: settled after the seed, not settled before its consume, settled after;
#   - the board route ledger maximum is 1 on Kobo D13 (Cold D13 and EV D9 are void per MD0-S2);
#   - gap lines over real readings (phase-2c open question 2).
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_ch5a1_board_contract import DELETED
    from test_out_b4_board_postgres import _settle_chain
    from test_s1_bindings_postgres import engine  # noqa: F401
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_apply_postgres import T_APPLY, accepted, apply, applying, current_foundation
    from test_s6_action_store_postgres import CASES

    import pg_harness
    from assetops_backend import read_scope
    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.composition import build_thread_sources
    from assetops_backend.chain.measures import measures_for
    from assetops_backend.chain.reader import SnapshotReader
    from assetops_backend.chain.read import ChainReader
    from assetops_backend.scheduling import stages
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

CODE = "KOBO-001"
DOMAIN, ANALYTIC = "mini_grid", "dispatch"
LO, HI = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 11, 1, tzinfo=timezone.utc)
DAY_LO, DAY_HI = date(2026, 10, 1), date(2026, 11, 3)
MEASURES = tuple(m.key for m in measures_for("MINIGRID"))
STATE: dict = {}  # cuts and ids shared by the ordered tests


@pytest.fixture(scope="module")
def world(engine):  # noqa: F811
    pg_harness.empty_tables(engine, ("foundation_revision", "source", "gateway", "asset", "site_import", "site",
                                     "tenant"))
    store = PostgresFoundationStore(URL)
    runner = CaseRunner(store, engine)
    run_case(runner, CASES["F01"])
    run_case(runner, CASES["F02"])
    _settle_chain(URL, CODE)
    snapshots = PostgresSnapshotStore(URL)
    port = PostgresChainRead(URL, snapshots=SnapshotReader(snapshots))
    threads = build_thread_sources(URL)
    try:
        yield runner, port, snapshots, threads
    finally:
        pg_harness.dispose(runner.findings, port, snapshots, threads, store)


def _consume(runner) -> dict:
    out = stages.chain_threads(URL, {"tenant_id": str(runner.tenant), "site_id": str(runner.site)})
    assert out["code"] == "OK" and out["deferred"] == 0, out
    return out


def _outbox(runner) -> list:
    with runner.engine.connect() as c:
        return [tuple(r) for r in c.execute(text(
            "SELECT o.type, o.occurred_at, o.site_id = :s, EXISTS (SELECT 1 FROM event_consumption x WHERE "
            "x.consumer = 'threads' AND x.event_id = o.event_id) FROM event_outbox o WHERE o.type = 'finding.revised' "
            "ORDER BY o.occurred_at"), {"s": runner.site})]


def _heads(world, k=None) -> dict[str, tuple]:
    runner, port, _, _ = world
    return {h.finding_id.lower(): (h.revision_id.lower(), h.revision_no, h.thread_id, h.occurrence_no)
            for h in port.finding_heads(runner.tenant, runner.site, DOMAIN, ANALYTIC, LO, HI, k)}


def _expected_heads(world, k=None) -> dict[str, tuple]:
    """The head rule computed in Python from the raw rows (independent of `_FINDING_HEADS`)."""
    runner = world[0]
    rows = runner.reload()
    with runner.engine.connect() as c:
        occ = {str(r[0]).lower(): (str(r[1]), r[2], r[3]) for r in c.execute(text(
            "SELECT finding_id, thread_id, occurrence_no, coalesce(source_known_at, joined_at) "
            "FROM finding_thread_occurrence WHERE site_id = :s AND finding_id IS NOT NULL"), {"s": runner.site})}
        merged = {str(r[0]).lower() for r in c.execute(text(
            "SELECT superseded_finding_id FROM finding_merge WHERE site_id = :s"), {"s": runner.site})}
    out = {}
    for f in rows["findings"]:
        fid = str(f["id"]).lower()
        if fid in merged or fid not in occ or f["domain"] != DOMAIN or f["analytic_id"] != ANALYTIC:
            continue
        tid, no, visible = occ[fid]
        if k is not None and visible > k:
            continue
        revs = [r for r in rows["revisions"] if r["finding_id"] == f["id"] and (k is None or r["created_at"] <= k)]
        if not revs:
            continue
        head = max(revs, key=lambda r: r["revision_no"])
        if head["episode_start"] < HI and (head["episode_end"] is None or head["episode_end"] > LO):
            out[fid] = (str(head["id"]).lower(), head["revision_no"], tid, no)
    return out


# ------------------------------------------------------------------ read-only checks on the settled seed

def test_snapshots_return_the_latest_row_per_key(world) -> None:
    runner, port, _, _ = world
    got = port.snapshots(runner.tenant, runner.site, DAY_LO, DAY_HI, MEASURES, None)
    assert got, "step (a) wrote no snapshots"
    assert isinstance(got, tuple)
    with runner.engine.connect() as c:
        raw = c.execute(text("SELECT local_day, subject_kind, subject_ref, measure, revision, grade "
                             "FROM site_day_snapshot WHERE site_id = :s AND local_day BETWEEN :lo AND :hi "
                             "AND measure = ANY(:m)"), {"s": runner.site, "lo": DAY_LO, "hi": DAY_HI,
                                                        "m": list(MEASURES)}).all()
    latest: dict[tuple, tuple] = {}
    for d, kind, ref, m, rev, grade in raw:
        key = (d, kind, ref, m)
        if key not in latest or rev > latest[key][0]:
            latest[key] = (rev, grade)
    assert {(r.local_day, r.subject_kind, r.subject_ref, r.measure): (r.revision, r.grade) for r in got} == latest
    assert {r.measure for r in got} <= set(MEASURES)


def test_finding_heads_follow_the_index_head_rule(world) -> None:
    heads = _heads(world)
    assert len(heads) == 2, heads  # F01 and F02
    assert heads == _expected_heads(world)
    runner, port, _, _ = world
    rows = port.finding_heads(runner.tenant, runner.site, DOMAIN, ANALYTIC, LO, HI, None)
    assert [h.episode_start for h in rows] == sorted((h.episode_start for h in rows), reverse=True)
    assert len({h.thread_id for h in rows}) == 1  # one generator thread
    assert sorted(h.occurrence_no for h in rows) == [1, 2]
    assert port.finding_heads(runner.tenant, runner.site, "cold_chain", ANALYTIC, LO, HI, None) == ()


def test_findings_settled_after_the_seed(world) -> None:
    runner, port, _, _ = world
    assert port.findings_settled(runner.tenant, runner.site, None) is True


def test_board_route_has_one_read_per_key_and_no_deleted_read(world, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from assetops_backend.config import load_feature_flags
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.main import create_app

    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "0" * 64)
    seen: list = []
    real = read_scope.scope

    @contextmanager
    def spy(route):  # perf.route opens the request's scope through this module attribute (perf.py:133)
        with real(route) as sc:
            seen.append(sc)
            yield sc

    monkeypatch.setattr(read_scope, "scope", spy)
    with TestClient(create_app(load_feature_flags())) as c:
        r = c.get(f"/api/sites/{CODE}/outcome-board", params={"date": "2026-10-06"})
    assert r.status_code == 200, r.text
    assert seen, "the board route opened no read scope"
    sc = seen[0]
    names = sc.names()
    assert any(n.startswith("chain.") for n in names), names  # the board read the chain (set non-empty)
    assert not [n for n in DELETED if n in names], names
    assert sc.max_per_key() == 1, sc.repeated()


# ------------------------------------------------------------------ appending checks (file order)

def test_known_at_hides_a_later_snapshot_selection(world) -> None:
    runner, port, snapshots, _ = world
    rows = port.snapshots(runner.tenant, runner.site, date(2026, 10, 6), date(2026, 10, 6), MEASURES, None)
    old = rows[0]
    with runner.engine.connect() as c:
        k = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    grade = "LOW" if old.grade != "LOW" else "PARTIAL"
    snapshots.append(replace(old, revision=old.revision + 1, grade=grade, expected=True, computed_at=None,
                             input_fp=hashlib.sha256(b"ch5a1-l2-selection").hexdigest()))

    def pick(known_at):
        got = port.snapshots(runner.tenant, runner.site, old.local_day, old.local_day, (old.measure,), known_at)
        return {(r.subject_kind, r.subject_ref): (r.revision, r.grade) for r in got}[(old.subject_kind,
                                                                                         old.subject_ref)]

    assert pick(k) == (old.revision, old.grade)
    assert pick(None) == (old.revision + 1, grade)


def test_known_at_hides_a_later_occurrence_and_revision_and_r8_tracks_the_consume(world) -> None:
    runner, port, _, threads = world
    f01 = next(iter(_heads(world)))  # any of the two; the L5 count is per thread
    k1 = runner.now
    steps = CASES["F04"]["steps"]
    first = next(i for i, s in enumerate(steps) if s["do"] == "match") + 1
    for step in steps[:first]:
        runner.step(step)

    # R8: the new finding.revised event is unconsumed, so the Findings are not settled; the consume settles them.
    assert port.findings_settled(runner.tenant, runner.site, None) is False, _outbox(runner)
    _consume(runner)
    assert port.findings_settled(runner.tenant, runner.site, None) is True
    k2 = runner.now
    after_first = _heads(world)
    [f04] = set(after_first) - set(_heads(world, k1))
    assert after_first[f04][1] == 1

    for step in steps[first:]:
        runner.step(step)
    assert port.findings_settled(runner.tenant, runner.site, None) is False
    _consume(runner)
    assert port.findings_settled(runner.tenant, runner.site, None) is True

    now = _heads(world)
    assert now == _expected_heads(world) and now[f04][1] >= 2, now
    # a later occurrence is hidden at k1, a later revision at k2
    assert f04 not in _heads(world, k1) and _heads(world, k1) == _expected_heads(world, k1)
    assert _heads(world, k2)[f04][:2] == after_first[f04][:2]
    assert _heads(world, k2) == _expected_heads(world, k2)

    # L5: the occurrence count at k1 excludes the third occurrence (F04 on the F01/F02 generator thread).
    tid = now[f01][2]
    assert now[f04][2] == tid and now[f04][3] == 3, now
    at_k1 = threads.lookup(runner.tenant, [f01], [], known_at=k1)["findings"][f01]
    at_now = threads.lookup(runner.tenant, [f01], [], known_at=None)["findings"][f01]
    assert (at_k1["occurrences"], at_now["occurrences"]) == (2, 3), (at_k1, at_now)

    # the R8 cut at k1 ignores the later events (occurred after it) once they are consumed, and the reader agrees
    req = ChainReader(port).request(runner.tenant, k1)
    assert req.findings_settled(runner.site) is True
    assert {h.finding_id.lower() for h in req.findings(runner.site, DOMAIN, ANALYTIC, LO, HI)} == set(
        _heads(world, k1))


def test_has_change_equals_the_detail_change_for_each_action(world) -> None:
    """Last: the APPLY publishes a new reserve FoundationRevision. Observed when it ran before the F04 test: F04's
    first match then left no unconsumed `finding.revised`, so the R8 step there could not be shown."""
    runner, port, _, _ = world
    h = applying(runner)
    try:
        action_id, _ = accepted(h, "2026-10-06")

        def parity(expected: bool) -> None:
            detail = h.client.get(f"/api/sites/{CODE}/actions/{action_id}")
            assert detail.status_code == 200, detail.text
            got = port.has_change(runner.tenant, [action_id])
            assert dict(got) == {action_id.lower(): bool(detail.json()["change"])}
            assert got[action_id.lower()] is expected

        parity(False)  # ACCEPTED only: no policy change
        h.clock.at = T_APPLY
        made = apply(h, action_id, current_foundation(h, action_id), "apply-ch5a1")
        assert made.status_code == 201, made.text
        parity(True)
        with pytest.raises(TypeError):
            port.has_change(runner.tenant, [action_id])[action_id.lower()] = False  # frozen
        assert dict(port.has_change(runner.tenant, [])) == {}
    finally:
        h.close()
