"""CH-5c (CH5c-R5 R5-1): the stored route responses over the real store and change log.

The route is the real estate Findings router (`estate_api.py`) with a composer that reads the real `site` table, so
a stored body can be checked against a fresh compose, a data change, an equivalent request, the admission in the
key, and the R5-1(e) race: a change committed between the watermark and the compose is served and never stored.
The real-data stored-equals-fresh check over every pre-built route is L3 (`tools/chain_response_probe.py`).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from test_s1_bindings_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_ch5c_watermark_postgres import _outbox, _seed
    from test_s1_bindings_postgres import engine  # noqa: F401

    from assetops_backend.chain import prebuild
    from assetops_backend.chain.adapters.postgres_response_store import PostgresResponseRows
    from assetops_backend.chain.composition import code_version
    from assetops_backend.chain.response_store import HEADER, ResponseStore, render
    from assetops_backend.chain.watermark import SERVE_KEYS
    from assetops_backend.estate_api import build_estate_router

Q = "/api/estate/findings?from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z"
WALL = ("known_at", "selection_token")  # Q4: the only wall-clock fields of a stored body


class Composer:
    """A Findings composer over the real `site` rows of the admitted Sites; `during` runs mid-compose."""

    def __init__(self, engine) -> None:  # noqa: F811
        self.engine, self.calls, self.during = engine, 0, None

    def findings(self, tenant, parsed, admit):
        self.calls += 1
        with self.engine.connect() as c:
            rows = c.execute(text("SELECT site_code, name FROM site WHERE tenant_id = :t ORDER BY site_code"),
                             {"t": tenant}).all()
        if self.during is not None:
            self.during()
        return {"rows": [{"site_code": r.site_code, "name": r.name} for r in rows if admit(r.site_code)],
                "total_count": None, "lens": parsed.lens, "limit": parsed.limit,
                "known_at": datetime.now(timezone.utc).isoformat(), "selection_token": uuid4().hex}


def _client(engine, tenant, composer, *, stored=True, deny=()):  # noqa: F811
    app = FastAPI()
    app.include_router(build_estate_router(
        composer, lambda: tenant, access=lambda request, code: 403 if code in deny else None,
        responses=_store(engine) if stored else None))
    return TestClient(app)


def _store(engine):  # noqa: F811
    return ResponseStore(PostgresResponseRows(engine=engine), code_version)


def _rows(engine, tenant):  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT route, request_key, watermark, etag, body FROM chain_response "
                              "WHERE tenant_id = :t ORDER BY built_at"), {"t": tenant}).all()


def _quiet(body: bytes) -> dict:
    doc = json.loads(body)
    return {k: v for k, v in doc.items() if k not in WALL}


def test_stored_bytes_are_served_and_equal_a_fresh_compose(engine) -> None:  # noqa: F811
    tenant, _ = _seed(engine)
    composer = Composer(engine)
    client = _client(engine, tenant, composer)
    first = client.get(Q)
    assert first.status_code == 200 and first.headers[HEADER] == "stored"
    second = client.get(Q)
    assert second.headers[HEADER] == "hit" and composer.calls == 1
    assert second.content == first.content and second.headers["etag"] == first.headers["etag"]
    (row,) = _rows(engine, tenant)
    assert bytes(row.body) == first.content and first.headers["etag"] == f'"{row.etag}"'
    # The stored bytes are FastAPI's own rendering of the composed body (serialised once).
    assert bytes(row.body) == render(json.loads(first.content))
    # Stored equals fresh: a store-less compose differs only in the Q4 wall-clock fields.
    fresh = _client(engine, tenant, Composer(engine), stored=False).get(Q)
    assert fresh.status_code == 200 and HEADER not in fresh.headers
    assert _quiet(fresh.content) == _quiet(second.content)
    assert set(json.loads(fresh.content)) == set(json.loads(second.content))


def test_a_data_change_recomposes_and_an_equivalent_request_hits(engine) -> None:  # noqa: F811
    tenant, sites = _seed(engine)
    composer = Composer(engine)
    client = _client(engine, tenant, composer)
    before = client.get(Q)
    # The parsed request is the key: the defaulted `lens` and `limit` spelled out are the same request.
    same = client.get(Q + "&lens=all&limit=50")
    assert same.headers[HEADER] == "hit" and same.content == before.content
    with engine.begin() as c:
        c.execute(text("UPDATE site SET name = 'Renamed' WHERE id = :s"), {"s": sites[1]})
    after = client.get(Q)
    assert after.headers[HEADER] == "stored" and composer.calls == 2
    assert [r["name"] for r in json.loads(after.content)["rows"]].count("Renamed") == 1  # never the stale body
    assert after.headers["etag"] != before.headers["etag"]


def test_admission_is_in_the_key(engine) -> None:  # noqa: F811
    tenant, _ = _seed(engine)
    full = _client(engine, tenant, Composer(engine)).get(Q)
    narrow = _client(engine, tenant, Composer(engine), deny=("CH5C-1",)).get(Q)
    assert narrow.headers[HEADER] == "stored"  # a different admitted set is a different key, never a hit
    assert "CH5C-1" in full.text and "CH5C-1" not in narrow.text
    keys = [r.request_key for r in _rows(engine, tenant)]
    assert len(set(keys)) == 2


def test_a_change_committed_during_the_compose_is_served_and_not_stored(engine) -> None:  # noqa: F811
    """R5-1(e): a change-log write commits between the watermark transaction and the after-check."""
    tenant, sites = _seed(engine)
    composer = Composer(engine)

    def change() -> None:
        with engine.begin() as c:
            _outbox(c, tenant, sites[0], f"race-{uuid4().hex}")

    composer.during = change
    client = _client(engine, tenant, composer)
    raced = client.get(Q)
    assert raced.status_code == 200 and raced.headers[HEADER] == "race"
    assert json.loads(raced.content)["rows"]  # the body is served
    assert _rows(engine, tenant) == []  # and nothing is stored
    composer.during = None
    quiet = client.get(Q)
    assert quiet.headers[HEADER] == "stored" and len(_rows(engine, tenant)) == 1


def test_prune_keeps_the_latest_three_per_route_and_key(engine) -> None:  # noqa: F811
    tenant = uuid4()
    route, key = f"/test/{tenant.hex}", "k"
    with engine.begin() as c:
        for i in range(5):
            c.execute(text("INSERT INTO chain_response (tenant_id, route, request_key, watermark, code_version, etag, "
                           "body, build_ms, built_at) VALUES (:t, :r, :k, :w, 'v', 'e', '\\x7b7d', 1, "
                           "now() + make_interval(secs => :i))"), {"t": tenant, "r": route, "k": key, "w": f"cic:{i}",
                                                                   "i": i})
    assert _store(engine).prune() >= 2
    assert [r.watermark for r in _rows(engine, tenant)] == ["cic:2", "cic:3", "cic:4"]


def test_prune_keeps_each_code_version_apart(engine) -> None:  # noqa: F811
    """CH5c-R6: version-A rows are never evicted by version-B inserts; each version keeps its own latest 3."""
    tenant = uuid4()
    route, key = f"/test/{tenant.hex}", "k"
    rows = [("A", 0), ("A", 1), ("A", 2)] + [("B", 10 + i) for i in range(5)]  # B is newer than every A row
    with engine.begin() as c:
        for version, i in rows:
            c.execute(text("INSERT INTO chain_response (tenant_id, route, request_key, watermark, code_version, etag, "
                           "body, build_ms, built_at) VALUES (:t, :r, :k, :w, :v, 'e', '\\x7b7d', 1, "
                           "now() + make_interval(secs => :i))"),
                      {"t": tenant, "r": route, "k": key, "w": f"cic:{i}", "v": version, "i": i})
    _store(engine).prune()
    with engine.connect() as c:
        kept = c.execute(text("SELECT code_version, watermark FROM chain_response WHERE tenant_id = :t "
                              "ORDER BY built_at"), {"t": tenant}).all()
    assert [(r.code_version, r.watermark) for r in kept] == [
        ("A", "cic:0"), ("A", "cic:1"), ("A", "cic:2"), ("B", "cic:12"), ("B", "cic:13"), ("B", "cic:14")]


def test_a_keyless_prebuild_stores_nothing_and_reports_the_skip(engine, monkeypatch) -> None:  # noqa: F811
    """CH5c-R6: a pre-build in a process without every serve key stores 0 rows and reports SKIPPED_NO_SERVE_ENV."""
    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", "on")  # CH5c-R7: the store is off unless opted in
    for name in SERVE_KEYS:
        monkeypatch.setenv(name, "1a" * 32)
    monkeypatch.delenv(SERVE_KEYS[0])
    with engine.connect() as c:
        before = c.execute(text("SELECT count(*) FROM chain_response")).scalar_one()

    class Never:
        def get(self, path):  # a skipped pre-build sends no request
            raise AssertionError(path)

    result = prebuild.run(URL, Never())
    with engine.connect() as c:
        after = c.execute(text("SELECT count(*) FROM chain_response")).scalar_one()
    assert result["code"] == "SKIPPED_NO_SERVE_ENV" and result["missing"] == [SERVE_KEYS[0]]
    assert result["requests"] == 0 and len(result["code_version"]) == 16 and after == before


def test_prebuild_paths_cover_every_listed_request_and_the_scope_ids() -> None:
    paths = prebuild.paths()
    portfolios = [p for p in paths if p.startswith("/api/estate/portfolio?")]
    assert len(paths) == len(set(paths)) and portfolios
    assert len([p for p in paths if p.startswith("/api/estate/portfolio/scope-ids?")]) == len(portfolios)
