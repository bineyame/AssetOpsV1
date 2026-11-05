"""CH-5b2 L2m (build sheet CH-5b §5 item 2, CH-5b2 acceptance; rulings CH5b2-R): the "Why?" trace and the stored
chain routes on a fresh MD-0 mechanism clone (`test_md0_mechanism_postgres.mech`), store ON.

- Kobo D13 OPTIMIZE_COST: the trace's own work (`ChainRequest.trace_facts` + `why.trace`, the reads included, the
  route admission and the Site chain reads it shares excluded) is <= 50 ms, the median of 5 requests (reported as
  `why_trace_ms`); its nodes carry the Findings it reaches and ACT-K1 with its verification.
- A `304` round trip on every chain and "Why?" route; the `304` runs only the store's (a) statements (the
  watermark first, the admitted Site set, one `chain_response` lookup) and opens no compose scope (CH5c2-R2 item 5).
- `trace_facts` is one statement per request (the ledger and the statement listener).
- After `late_fill(KOBO-001, D7)` and its consume, the Kobo tag changes and the old tag is no longer a 304.

One clone, one test (the clone and derive dominate the cost).
"""
from __future__ import annotations

import json
import statistics
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    from test_md0_mechanism_postgres import mech  # noqa: F401  (the clone + derive fixture)
    from test_out_b4_board_postgres import _settle_chain

    import mechanism_dataset as md
    from assetops_backend import read_scope
    from assetops_backend.chain import why
    from assetops_backend.chain.read import ChainRequest

SPEC = md.load() if URL else None
OUT = Path(__file__).resolve().parents[2] / "var" / "ch5b2_why_postgres.json"
CODE = "KOBO-001"


def _app(url: str, store: str):
    from fastapi.testclient import TestClient

    from assetops_backend.config import load_feature_flags
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.main import create_app

    mp = pytest.MonkeyPatch()
    mp.setenv("DATABASE_URL", url)
    mp.setenv(PORTFOLIO_CURSOR_KEY_ENV, "0" * 64)
    mp.setenv("ASSETOPS_RESPONSE_STORE", store)
    return mp, TestClient(create_app(load_feature_flags()))


@contextmanager
def _statements():
    seen: list[str] = []

    def listener(conn, cursor, statement, params, context, many):  # noqa: ANN001
        seen.append(statement)

    event.listen(Engine, "before_cursor_execute", listener)
    try:
        yield seen
    finally:
        event.remove(Engine, "before_cursor_execute", listener)


def test_why_trace_and_304_on_the_mechanism_site(mech, monkeypatch) -> None:  # noqa: F811
    engine, m = mech
    url = engine.url.render_as_string(hide_password=False)
    _settle_chain(url, CODE)
    d13 = md.day(SPEC, 13).isoformat()
    report: dict = {"day": d13}

    # 1. why_trace_ms: the trace's own reads and build, 5 requests with the store off.
    spent: list[float] = []
    ledgers: list[dict] = []
    real_trace, real_facts = why.trace, ChainRequest.trace_facts

    def timed_facts(self, site_id, finding_ids):
        t0 = time.perf_counter()
        try:
            return real_facts(self, site_id, finding_ids)
        finally:
            spent[-1] += (time.perf_counter() - t0) * 1000

    def timed_trace(x):
        t0 = time.perf_counter()
        try:
            return real_trace(x)
        finally:
            spent[-1] += (time.perf_counter() - t0) * 1000

    real_scope = read_scope.scope

    @contextmanager
    def spy(route):
        with real_scope(route) as sc:
            yield sc
            ledgers.append(sc.names())

    monkeypatch.setattr(why, "trace", timed_trace)
    monkeypatch.setattr(ChainRequest, "trace_facts", timed_facts)
    monkeypatch.setattr(read_scope, "scope", spy)
    mp, off = _app(url, "off")
    try:
        with off:
            body = None
            for _ in range(5):
                spent.append(0.0)
                with _statements() as stmts:
                    r = off.get(f"/api/sites/{CODE}/chain/why", params={"date": d13, "category": "OPTIMIZE_COST"})
                assert r.status_code == 200, r.text
                body = r.json()
                n_facts = sum("finding_revision_evidence" in s and "LATERAL" in s for s in stmts)
                assert n_facts == 1, (n_facts, body["text"], [(n["kind"], n["ids"][:2]) for n in body["nodes"]])
    finally:
        mp.undo()
    monkeypatch.setattr(read_scope, "scope", real_scope)
    assert all(lg.get("chain.trace_facts", 0) <= 1 for lg in ledgers), ledgers  # Q4: one statement per request
    report["why_trace_ms_runs"] = [round(x, 2) for x in spent]
    report["why_trace_ms"] = round(statistics.median(spent), 2)
    report["text"] = body["text"]
    report["nodes"] = [{k: n[k] for k in ("kind", "ids", "basis")} for n in body["nodes"]]
    ids = {i for n in body["nodes"] for i in n["ids"]}
    reached = {a: f in ids for a, f in m["findings"].items()}
    report["findings_reached"] = reached
    act = next((n for n in body["nodes"] if n["kind"] == "action" and m["action"]["action_id"] in n["ids"]), None)
    report["act_k1"] = act
    assert all(n["ids"] for n in body["nodes"][1:])
    assert reached.get("K-OVR-D4") and reached.get("K-OVR-D11"), reached
    assert act is not None and act["basis"]["verification"] is not None, act
    assert report["why_trace_ms"] <= 50, report["why_trace_ms_runs"]

    # 2. 304 on every route, store on.
    mp, on = _app(url, "on")
    try:
        with on:
            q = {"date": d13}
            chain = on.get(f"/api/sites/{CODE}/chain", params=q)
            assert chain.status_code == 200, chain.text
            tid = chain.json()["threads"][0]["id"]
            day = f"{d13}T00:00:00Z"
            nxt = f"{md.day(SPEC, 14).isoformat()}T00:00:00Z"
            routes = {"site_chain": (f"/api/sites/{CODE}/chain", q),
                      "site_why": (f"/api/sites/{CODE}/chain/why", {**q, "category": "OPTIMIZE_COST"}),
                      "thread": (f"/api/sites/{CODE}/threads/{tid}", q),
                      "estate_chain": ("/api/estate/chain", {"from": day, "to": nxt}),
                      "estate_why": ("/api/estate/chain/why", {"from": day, "to": nxt, "category": "PROTECT_ASSET"})}
            tags, statements = {}, {}
            for name, (path, params) in routes.items():
                first = on.get(path, params=params)
                assert first.status_code == 200 and first.headers.get("etag"), (name, first.status_code, first.text)
                tags[name] = first.headers["etag"]
                opened: list = []
                real_fresh = read_scope.fresh

                @contextmanager
                def fresh_spy(route, opened=opened, real_fresh=real_fresh):
                    with real_fresh(route) as sc:
                        opened.append(route)
                        yield sc

                monkeypatch.setattr(read_scope, "fresh", fresh_spy)
                with _statements() as stmts:
                    r = on.get(path, params=params, headers={"If-None-Match": tags[name]})
                monkeypatch.setattr(read_scope, "fresh", real_fresh)
                assert r.status_code == 304 and r.content == b"", (name, r.status_code)
                assert r.headers["etag"] == tags[name] and r.headers["cache-control"] == "private, no-cache"
                assert opened == [], (name, opened)  # no composition
                tables = [s for s in stmts if " FROM " in s.upper()]
                # The route's admission (the Site registry: tenant, site) runs first, as on every request; the store's
                # (a) then runs the watermark first, the admitted Site set and one `chain_response` lookup, and nothing
                # runs after it (no composition).
                at = next(i for i, s in enumerate(tables) if "chain_input_change" in s)
                admission, store = tables[:at], tables[at:]
                statements[name] = {"admission": [s.split(" WHERE ")[0][:60] for s in admission],
                                    "store": [s.split(" WHERE ")[0][:60] for s in store]}
                assert all(" FROM tenant " in s or " FROM site " in s or "FROM site\n" in s for s in admission), \
                    (name, admission)
                # An estate route's admitted Site set also runs its admission per Site (`admit`, the registry reads).
                assert "chain_response" in store[-1] and sum("chain_response" in s for s in store) == 1, (name, store)
                assert all(" FROM site " in s or " FROM tenant " in s for s in store[1:-1]), (name, store)
                assert len(store) == 3 or name.startswith("estate"), (name, store)
            report["etag_304_statements"] = statements

            # 3. late_fill(KOBO-001, D7) and its consume: the Kobo tag changes.
            out = md.late_fill(url, CODE, 7)
            md.drain_mini(url)
            md.derive(url, uuid.UUID(out["tenant_id"]), uuid.UUID(out["site_id"]))
            _settle_chain(url, CODE)
            path, params = routes["site_chain"]
            after = on.get(path, params=params, headers={"If-None-Match": tags["site_chain"]})
            assert after.status_code == 200 and after.headers["etag"] != tags["site_chain"], after.status_code
            report["late_fill"] = {"before": tags["site_chain"], "after": after.headers["etag"]}
    finally:
        mp.undo()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
