"""CH-5c2 (CH5c-R7 M1, L1, H2 C1/C2/C4, L4; CH5c2-R1): the stored-response safety rules over the real store.

The route is the real estate Findings router with a composer that reads the real `site` table and, like the real
composers, compares a clock-derived instant only through `read_scope.within` (C1). It proves:

- M1: a failing port at the lookup, the (c) re-check or the insert serves a 200 with the composed body, `unstored`,
  no ETag, and stores nothing;
- L1: an insert whose `ON CONFLICT` inserted nothing sends no ETag;
- C2: the live row stores `valid_until` (the registered boundary - 1 s); a historical request stores NULL; moving
  the app clock (`read_scope.clock`) past it makes the next request a miss whose body shows the new label;
- L4: `TRUNCATE chain_input_change` is refused; under `session_replication_role = replica` (the W5 harness reset)
  it is allowed (rolled back here).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from test_s1_bindings_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_ch5c_watermark_postgres import _seed
    from test_s1_bindings_postgres import engine  # noqa: F401

    from assetops_backend import read_scope
    from assetops_backend.chain.adapters.postgres_response_store import PostgresResponseRows
    from assetops_backend.chain.composition import code_version
    from assetops_backend.chain.response_store import HEADER, MARGIN, ResponseStore
    from assetops_backend.estate_api import build_estate_router

Q = "/api/estate/findings?from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z"
#: The plan window end the composer compares against (a C1 boundary): after the real DB clock (the lookup takes the
#: later of both clocks) and away from a UTC midnight.
END = datetime(2036, 11, 5, 15, 0, tzinfo=timezone.utc)


class Composer:
    """Findings over the real `site` rows, labelled `OPEN` while `read_scope.clock()` is inside [START, END)."""

    def __init__(self, engine) -> None:  # noqa: F811
        self.engine, self.calls = engine, 0

    def findings(self, tenant, parsed, admit):
        self.calls += 1
        with self.engine.connect() as c:
            rows = c.execute(text("SELECT site_code FROM site WHERE tenant_id = :t ORDER BY site_code"),
                             {"t": tenant}).all()
        at = parsed.known_at or read_scope.clock()
        label = "OPEN" if read_scope.within(END - timedelta(days=7), END, at) else "CLOSED"
        return {"rows": [{"site_code": r.site_code, "label": label} for r in rows if admit(r.site_code)],
                "total_count": None, "lens": parsed.lens, "limit": parsed.limit, "known_at": None,
                "selection_token": None}


class FailingRows:
    """The real port, failing at one call: `lookup` (the first read), `recheck` (the second read) or `insert`."""

    def __init__(self, rows, at: str) -> None:
        self.rows, self.at, self.reads = rows, at, 0

    def read(self, work):
        self.reads += 1
        if (self.at, self.reads) in (("lookup", 1), ("recheck", 2)):
            raise RuntimeError(f"planted {self.at} failure")
        return self.rows.read(work)

    def insert(self, *args, **kwargs):
        if self.at == "insert":
            raise RuntimeError("planted insert failure")
        return self.rows.insert(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.rows, name)


def _client(engine, tenant, composer, rows=None):  # noqa: F811
    app = FastAPI()
    store = ResponseStore(rows or PostgresResponseRows(engine=engine), code_version)
    app.include_router(build_estate_router(composer, lambda: tenant, access=lambda request, code: None,
                                           responses=store))
    return TestClient(app)


def _stored(engine, tenant):  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT etag, valid_until FROM chain_response WHERE tenant_id = :t ORDER BY built_at"),
                         {"t": tenant}).all()


@pytest.mark.parametrize("at", ["lookup", "recheck", "insert"])
def test_m1_a_failing_port_serves_the_composed_body_unstored(engine, monkeypatch, at) -> None:  # noqa: F811
    monkeypatch.setattr(read_scope, "clock", lambda: END - timedelta(days=1))
    tenant, _ = _seed(engine)
    expected = _client(engine, tenant, Composer(engine)).get(Q)  # a working store: the reference body
    with engine.begin() as c:
        c.execute(text("DELETE FROM chain_response WHERE tenant_id = :t"), {"t": tenant})
    out = _client(engine, tenant, Composer(engine), FailingRows(PostgresResponseRows(engine=engine), at)).get(Q)
    assert out.status_code == 200 and out.headers[HEADER] == "unstored"
    assert "etag" not in out.headers
    assert json.loads(out.content) == json.loads(expected.content)
    assert _stored(engine, tenant) == []


def test_l1_an_insert_that_inserted_nothing_sends_no_etag(engine, monkeypatch) -> None:  # noqa: F811
    monkeypatch.setattr(read_scope, "clock", lambda: END - timedelta(days=1))
    tenant, _ = _seed(engine)
    real = PostgresResponseRows(engine=engine)

    class Conflicting(FailingRows):
        def insert(self, *args, **kwargs):
            real.insert(*args, **kwargs)  # another writer stores the same key first
            return real.insert(*args, **kwargs)  # this insert's ON CONFLICT inserts nothing

    out = _client(engine, tenant, Composer(engine), Conflicting(real, "none")).get(Q)
    assert out.status_code == 200 and out.headers[HEADER] == "race" and "etag" not in out.headers
    assert len(_stored(engine, tenant)) == 1


def test_c2_valid_until_is_stored_and_a_moved_clock_misses(engine, monkeypatch) -> None:  # noqa: F811
    now = {"t": END - timedelta(hours=2)}
    monkeypatch.setattr(read_scope, "clock", lambda: now["t"])
    tenant, _ = _seed(engine)
    composer = Composer(engine)
    client = _client(engine, tenant, composer)
    first = client.get(Q)
    assert first.headers[HEADER] == "stored" and {r["label"] for r in json.loads(first.content)["rows"]} == {"OPEN"}
    ((_, until),) = _stored(engine, tenant)
    assert until == END - MARGIN  # the window end, not the later midnight cap
    now["t"] = END - timedelta(minutes=30)
    assert client.get(Q).headers[HEADER] == "hit" and composer.calls == 1  # still before valid_until
    now["t"] = END  # across the plan-window end
    moved = client.get(Q)
    assert moved.headers[HEADER] == "stored" and composer.calls == 2
    assert {r["label"] for r in json.loads(moved.content)["rows"]} == {"CLOSED"}
    # The expired row is replaced under the same W (the re-warm stores), with a new tag and a later expiry.
    assert moved.headers["etag"] != first.headers["etag"]
    ((tag, until2),) = _stored(engine, tenant)
    assert moved.headers["etag"] == f'"{tag}"' and until2 > until
    assert client.get(Q).headers[HEADER] == "hit"


def test_c2_a_historical_request_never_expires(engine, monkeypatch) -> None:  # noqa: F811
    monkeypatch.setattr(read_scope, "clock", lambda: END - timedelta(hours=2))
    tenant, _ = _seed(engine)
    out = _client(engine, tenant, Composer(engine)).get(Q + "&known_at=2026-11-01T00:00:00Z")
    assert out.headers[HEADER] == "stored"
    ((_, until),) = _stored(engine, tenant)
    assert until is None


def test_l4_truncate_of_the_change_log_is_refused_and_replica_is_allowed(engine) -> None:  # noqa: F811
    _seed(engine)
    with pytest.raises(DBAPIError, match="append-only|append only|refused|ledger"):
        with engine.begin() as c:
            c.execute(text("TRUNCATE chain_input_change"))
    with engine.connect() as c:
        tx = c.begin()
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("TRUNCATE chain_input_change"))
        assert c.execute(text("SELECT count(*) FROM chain_input_change")).scalar_one() == 0
        tx.rollback()
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM chain_input_change")).scalar_one() > 0
