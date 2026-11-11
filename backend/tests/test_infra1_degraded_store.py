"""INFRA-1 (D-E5.47, no database): an infrastructure read failure is never stored and never shown as a data fact.

T1 a connection failure mid-compose stores nothing and the old copy keeps serving (`stale`, no ETag); T2 with no
old copy, a 503 `TEMPORARILY_UNAVAILABLE` and nothing stored; T3 a bare `LedgerUnavailable` keeps its honest
PARTIAL and is stored; T4 the `is_transient` table; T6 the prebuild retries a degraded path, reports `DEGRADED` when
it stays degraded, and `demo_combined` then exits non-zero. (T5, the `handle_error` hook, is the Postgres file
`test_infra1_handle_error_postgres.py`; T7 is the frontend `temporarilyUnavailable.test.tsx`.)
"""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import psycopg
import pytest
from sqlalchemy import exc as sa_exc

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from assetops_backend import read_scope  # noqa: E402
from assetops_backend.chain import prebuild  # noqa: E402
from assetops_backend.chain.response_store import HEADER, ResponseStore, StoredRoute, request_key  # noqa: E402
from assetops_backend.evidence.ledger import LedgerUnavailable  # noqa: E402
from assetops_backend.infra import is_transient  # noqa: E402
from assetops_backend.site_outcomes.mini import Reads  # noqa: E402

TENANT = UUID("00000000-0000-0000-0000-000000000001")
SITE = "00000000-0000-0000-0000-0000000000aa"
ROUTE = "/api/estate/outcome-summary"
REQUEST = {"from": "2026-11-02", "to": "2026-11-09"}
OLD = b'{"sites":[{"site_code":"KOBO-001","read_state":"AVAILABLE"}]}'


def _too_many() -> sa_exc.OperationalError:
    return sa_exc.OperationalError("SELECT 1", {}, psycopg.OperationalError("too many clients already"))


class Snap:
    def __init__(self, rows: "Rows") -> None:
        self._rows = rows

    def watermark(self, tenant_id, site_ids):
        return self._rows.w

    def sites(self, tenant_id):
        return [(SITE, "KOBO-001", "UTC")]

    def lookup(self, route, key, watermark, version, now):
        return self._rows.live.get((route, key, watermark, version))


class Rows:
    """A `chain_response` port: `old` rows are earlier watermarks (never a live hit for the current W)."""

    def __init__(self, old: dict | None = None) -> None:
        self.w, self.live, self.old = "cic:2", {}, dict(old or {})
        self.inserted: list = []

    def read(self, work):
        return work(Snap(self))

    def insert(self, tenant_id, watermark, version, build_ms, until, rows, now=None):
        self.inserted += rows
        for route, key, tag, body in rows:
            self.live[(route, key, watermark, version)] = (body, tag)
        return {r[0] for r in rows}

    def latest_good(self, route, key, version):
        return self.old.get((route, key, version))

    def prune(self, keep):
        return 0

    def dispose(self):
        pass

    def connections(self):
        return 7


def _req() -> StoredRoute:
    return StoredRoute(ROUTE, TENANT, REQUEST, locale="en")


def _key() -> str:
    return request_key(ROUTE, TENANT, (SITE,), REQUEST, "en")


def _compose(fail: BaseException):
    """A compose whose second of three producer reads raises `fail`, halfway through (B.3: the read is a failed
    read name, the body PARTIAL)."""
    def compose():
        reads = Reads("KOBO-001")
        reads.call("site_registry", lambda: 1)
        def objectives():
            raise fail
        reads.call("objectives", objectives)
        reads.call("evidence", lambda: 2)
        state = "PARTIAL" if reads.failed else "AVAILABLE"
        return {ROUTE: {"sites": [{"site_code": "KOBO-001", "read_state": state}]}}
    return compose


def test_t1_connection_failure_mid_compose_stores_nothing_and_serves_the_old_copy() -> None:
    rows = Rows({(ROUTE, _key(), "v1"): OLD})
    r = ResponseStore(rows, lambda: "v1").serve(_req(), _compose(_too_many()))
    assert rows.inserted == []
    assert r.status_code == 200 and r.body == OLD
    assert r.headers[HEADER] == "stale" and "etag" not in r.headers and r.headers["retry-after"] == "30"


def test_t2_no_old_copy_is_a_503_and_nothing_stored() -> None:
    rows = Rows()
    r = ResponseStore(rows, lambda: "v1").serve(_req(), _compose(_too_many()))
    assert rows.inserted == []
    assert r.status_code == 503 and r.headers["retry-after"] == "5" and "etag" not in r.headers
    assert json.loads(r.body) == {"code": "TEMPORARILY_UNAVAILABLE",
                                  "message": "This view is temporarily unavailable. Retrying."}


def test_t2_compose_only_degraded_is_a_503() -> None:
    r = ResponseStore(Rows(), lambda: "v1", compose_only=True).serve(_req(), _compose(_too_many()))
    assert r.status_code == 503


def test_t2_a_transient_lookup_failure_composes_nothing_and_is_a_503() -> None:
    class Down(Rows):
        def read(self, work):
            raise _too_many()

    composed: list = []
    r = ResponseStore(Down(), lambda: "v1").serve(_req(), lambda: composed.append(1) or {})
    assert r.status_code == 503 and composed == []


def test_t3_a_bare_wrapper_keeps_its_honest_partial_and_is_stored() -> None:
    rows = Rows({(ROUTE, _key(), "v1"): OLD})
    r = ResponseStore(rows, lambda: "v1").serve(_req(), _compose(LedgerUnavailable("DATABASE_URL is not set")))
    assert r.status_code == 200 and r.headers[HEADER] == "stored" and "etag" in r.headers
    assert json.loads(r.body)["sites"][0]["read_state"] == "PARTIAL"
    assert len(rows.inserted) == 1 and rows.inserted[0][3] == r.body


def _wrapped(cause: BaseException) -> LedgerUnavailable:
    try:
        try:
            raise cause
        except BaseException as error:
            raise LedgerUnavailable("the ledger could not be read") from error
    except LedgerUnavailable as wrapper:
        return wrapper


def _implicit(cause: BaseException) -> LedgerUnavailable:
    try:
        try:
            raise cause
        except BaseException:
            raise LedgerUnavailable("the ledger could not be read")  # noqa: B904 - implicit `__context__`
    except LedgerUnavailable as wrapper:
        return wrapper


@pytest.mark.parametrize("error,want", [
    (_too_many(), True),
    (psycopg.errors.TooManyConnections("sorry, too many clients already"), True),
    (psycopg.OperationalError("connection refused"), True),
    (sa_exc.TimeoutError("QueuePool limit of size 5 overflow 10 reached"), True),  # the pool timeout
    (sa_exc.InterfaceError("SELECT 1", {}, Exception("closed")), True),
    (sa_exc.DisconnectionError("gone"), True),
    (ConnectionRefusedError("refused"), True),
    (socket.timeout("timed out"), True),
    (_wrapped(_too_many()), True),          # a wrapped cause
    (_implicit(sa_exc.TimeoutError("pool")), True),  # an implicit context
    (LedgerUnavailable("DATABASE_URL is not set"), False),  # a bare wrapper
    (LedgerUnavailable("tenant/Site not found"), False),
    (ValueError("bad"), False),
    (FileNotFoundError("manifest.json"), False),
    (sa_exc.ProgrammingError("SELECT x", {}, Exception("no column")), False),
    (None, False),
])
def test_t4_is_transient_table(error, want) -> None:
    assert is_transient(error) is want


def test_note_failure_marks_only_transient_and_only_in_a_scope() -> None:
    assert read_scope.note_failure("x", _too_many()) is False  # no scope
    with read_scope.fresh("r") as sc:
        assert read_scope.note_failure("objectives", LedgerUnavailable("DATABASE_URL is not set")) is False
        assert read_scope.note_failure("objectives", _too_many()) is True
        read_scope.note_failure("objectives", _too_many())
    assert sc.degraded == ["objectives"]


class Store:
    def __init__(self) -> None:
        self.pruned = self.disposed = 0

    def prune(self):
        self.pruned += 1
        return 0

    def dispose(self):
        self.disposed += 1

    def connections(self):
        return 42


class Client:
    def __init__(self, answers: list[tuple[int, str]]) -> None:
        self.answers, self.calls = list(answers), 0

    def get(self, path):
        self.calls += 1
        status, state = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        return SimpleNamespace(status_code=status, headers={HEADER: state})


@pytest.fixture
def prebuild_env(monkeypatch):
    from assetops_backend.chain.watermark import SERVE_KEYS

    monkeypatch.setenv("ASSETOPS_RESPONSE_STORE", "on")
    for k in SERVE_KEYS:
        monkeypatch.setenv(k, "x")
    monkeypatch.setattr(prebuild, "build_response_store", lambda url: Store())
    monkeypatch.setattr(prebuild, "paths", lambda: ["/api/estate/outcome-summary?from=a&to=b"])
    waits: list = []
    monkeypatch.setattr(prebuild, "_sleep", waits.append)
    return waits


def test_t6_a_503_once_then_200_retries_and_reports_ok(prebuild_env) -> None:
    client = Client([(503, "unavailable"), (200, "stored")])
    out = prebuild.run("postgresql://x", client)
    assert out["code"] == "OK" and client.calls == 2 and prebuild_env == [2]
    assert out["degraded"] == {"/api/estate/outcome-summary?from=a&to=b": 2} and out["pg_stat_activity"] == 42


def test_t6_a_stale_copy_is_retried_too(prebuild_env) -> None:
    out = prebuild.run("postgresql://x", Client([(200, "stale"), (200, "stale"), (200, "hit")]))
    assert out["code"] == "OK" and prebuild_env == [2, 5]


def test_t6_always_503_is_degraded_and_demo_combined_exits_non_zero(prebuild_env, monkeypatch, tmp_path) -> None:
    import demo_combined as tool

    client = Client([(503, "unavailable")])
    out = prebuild.run("postgresql://x", client)
    path = "/api/estate/outcome-summary?from=a&to=b"
    assert out["code"] == "DEGRADED" and client.calls == 4 and prebuild_env == [2, 5, 10]
    assert out["still_degraded"] == [path] and out["degraded"] == {path: 4}

    demo = object.__new__(tool.Demo)
    demo.work = demo.tree = tmp_path
    demo.story = lambda: {"sites": []}
    demo.read_site_mark = lambda site: None
    demo.write_prebuilt_routes = lambda: None
    demo.py = lambda *a, **k: SimpleNamespace(returncode=1, stdout=json.dumps(out))
    monkeypatch.setattr(tool, "performance_due", lambda *a: False)
    with pytest.raises(SystemExit) as exited:
        demo.performance_and_prebuild()
    assert "DEGRADED" in str(exited.value.code) and path in str(exited.value.code)  # a message: exit status 1

    from assetops_backend.scheduling import run as run_cli
    from assetops_backend.scheduling import stages

    monkeypatch.setattr(stages, "prebuild", lambda url, args: out)
    assert run_cli.main(["prebuild"]) == 1
