"""CH-5a2a L2 (build sheet Part B §B10 item 3): the three `/chain` routes under TestClient on Postgres.

Seeded as `test_ch5a1_reader_postgres.py` (the S4 F01/F02 generator thread on Kobo, then `_settle_chain`): the Site
chain on the day of the thread's first occurrence, the thread route, the estate chain, the refusals (a window over
31 days, a bad `known_at`, an unknown or foreign thread id -> 404 THREAD_NOT_FOUND) and the ledger maximum of 1
per (read, key) on every route. Read-only after the seed.
"""
from __future__ import annotations

from contextlib import contextmanager

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from test_out_b4_board_postgres import _settle_chain
    from test_s1_bindings_postgres import engine  # noqa: F401
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_store_postgres import CASES

    import pg_harness
    from assetops_backend import read_scope
    from assetops_backend.chain.lifecycle import local_day
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

CODE = "KOBO-001"
OTHER_THREAD = "00000000-0000-4000-8000-00000000dead"


@pytest.fixture(scope="module")
def world(engine):  # noqa: F811
    pg_harness.empty_tables(engine, ("foundation_revision", "source", "gateway", "asset", "site_import", "site",
                                     "tenant"))
    store = PostgresFoundationStore(URL)
    runner = CaseRunner(store, engine)
    run_case(runner, CASES["F01"])
    run_case(runner, CASES["F02"])
    _settle_chain(URL, CODE)
    with engine.connect() as c:
        tid, start, tz = c.execute(text(
            "SELECT CAST(o.thread_id AS text), o.episode_start, s.timezone FROM finding_thread_occurrence o "
            "JOIN site s ON s.id = o.site_id WHERE o.finding_id IS NOT NULL ORDER BY o.thread_id, o.occurrence_no "
            "LIMIT 1")).one()
    try:
        yield {"thread": tid, "day": local_day(start, tz).isoformat()}
    finally:
        pg_harness.dispose(runner.findings, store)


@pytest.fixture(scope="module")
def app(world):
    from fastapi.testclient import TestClient

    from assetops_backend.config import load_feature_flags
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.main import create_app

    mp = pytest.MonkeyPatch()
    mp.setenv("DATABASE_URL", URL)
    mp.setenv(PORTFOLIO_CURSOR_KEY_ENV, "0" * 64)
    try:
        with TestClient(create_app(load_feature_flags())) as c:
            yield c
    finally:
        mp.undo()


def _scoped(app, monkeypatch, path, params):
    seen: list = []
    real = read_scope.scope

    @contextmanager
    def spy(route):  # perf.route opens the request's scope through this module attribute
        with real(route) as sc:
            seen.append(sc)
            yield sc

    monkeypatch.setattr(read_scope, "scope", spy)
    r = app.get(path, params=params)
    assert r.status_code == 200, r.text
    assert seen, "the route opened no read scope"
    names = seen[0].names()
    assert any(n.startswith("chain.") for n in names), names
    assert seen[0].max_per_key() == 1, seen[0].repeated()
    return r.json()


def test_site_chain_lists_the_generator_thread_with_one_read_per_key(world, app, monkeypatch) -> None:
    body = _scoped(app, monkeypatch, f"/api/sites/{CODE}/chain", {"date": world["day"]})
    assert body["schema_version"] == "outcome-chain-1" and body["site"]["code"] == CODE
    assert [d["day"] for d in body["days"]] == [world["day"]]
    assert len(body["outcomes"]) == 4
    threads = {t["id"]: t for t in body["threads"]}
    assert world["thread"] in threads, sorted(threads)  # the set is non-empty
    t = threads[world["thread"]]
    assert t["state"] is not None and t["state_label"] and t["occurrences"], t
    assert t["ref"] == {"kind": "THREAD", "site": CODE, "id": world["thread"]}


def test_thread_route_reads_the_thread_and_its_events(world, app, monkeypatch) -> None:
    body = _scoped(app, monkeypatch, f"/api/sites/{CODE}/threads/{world['thread']}", {})
    thread = body["thread"]
    assert thread["id"] == world["thread"] and thread["events"], thread
    assert thread["events"][-1]["state"] == thread["state"]
    assert all(e["state_label"] for e in thread["events"])


def test_estate_chain_has_one_read_per_key_and_count_claims(app, monkeypatch) -> None:
    body = _scoped(app, monkeypatch, "/api/estate/chain",
                   {"from": "2026-10-01T00:00:00Z", "to": "2026-10-08T00:00:00Z"})
    # CH-5a2b (§B14 Q7): the four PC-1 count claims from the one computation, each with the summed day grades.
    assert set(body["counts"]) == {"count.open_threads", "count.verified_results", "count.opportunities",
                                 "count.sites_disrupted"}
    assert all(c["value"] is not None and c["basis"] in ("COMPLETE", "CHECKED_DAYS", "NOT_KNOWN") and c["text"]
               for c in body["counts"].values())
    kobo = next(s for s in body["sites"] if s["code"] == CODE)
    assert kobo["days"]["requested"] == 7 and set(kobo["rows"]) == {
        "GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"}


@pytest.mark.parametrize("path,params,status,code", [
    ("/api/estate/chain", {"from": "2026-09-01T00:00:00Z", "to": "2026-10-08T00:00:00Z"}, 422, "INVALID_WINDOW"),
    (f"/api/sites/{CODE}/chain", {"date": "2026-10-06", "known_at": "not-an-instant"}, 422, "INVALID_WINDOW"),
    (f"/api/sites/{CODE}/threads/{OTHER_THREAD}", {}, 404, "THREAD_NOT_FOUND"),
])
def test_refusals(app, path, params, status, code) -> None:
    r = app.get(path, params=params)
    assert r.status_code == status, r.text
    detail = r.json()["detail"]
    assert (detail.get("code") or detail.get("error", {}).get("code")) == code, detail
