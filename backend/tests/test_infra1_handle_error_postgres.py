"""INFRA-1 T5 (D-E5.47 rule 2, a `*_test` database): the global `handle_error` backstop marks the current read
scope when a connect is refused, and does not mark it for a good read or a statement error."""
from __future__ import annotations

import os
import socket

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy import exc as sa_exc
from sqlalchemy.engine import Engine, make_url

from assetops_backend import read_scope
from assetops_backend.chain.adapters import postgres_response_store as infra

#: Only `SELECT 1` and a statement error are run, on no table, so the base `*_test` database serves (the harness's
#: routed, migrated clone is not needed: `pg_harness` keeps the base URL in `ASSETOPS_TEST_DATABASE_BASE_URL`).
URL = os.environ.get("ASSETOPS_TEST_DATABASE_BASE_URL") or os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="needs ASSETOPS_TEST_DATABASE_URL (a *_test database)")


def _closed_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]  # closed again on exit: a connect is refused


def _refused(sc_route: str) -> read_scope.ReadScope:
    engine = create_engine(make_url(URL).set(host="127.0.0.1", port=_closed_port()),
                           connect_args={"connect_timeout": 3})
    try:
        with read_scope.fresh(sc_route) as sc:
            with pytest.raises(sa_exc.OperationalError):
                with engine.connect() as c:
                    c.execute(text("SELECT 1"))
        return sc
    finally:
        engine.dispose()


def test_t5_handle_error_marks_the_scope_on_a_refused_connect() -> None:
    assert make_url(URL).database.endswith("_test")
    infra.install_handle_error_hook()
    infra.install_handle_error_hook()  # idempotent
    good = create_engine(URL)
    try:
        with read_scope.fresh("good") as ok:
            with good.connect() as c:
                assert c.execute(text("SELECT 1")).scalar_one() == 1
                with pytest.raises(sa_exc.ProgrammingError):
                    c.execute(text("SELECT no_such_column FROM no_such_table"))
        assert ok.degraded == []  # a good read and a statement error mark nothing
    finally:
        good.dispose()
    assert _refused("refused").degraded == ["db.handle_error"]


def test_t5_without_the_hook_nothing_marks_the_scope() -> None:
    """Non-vacuous: the mark comes from the hook, not from the connect itself."""
    infra.install_handle_error_hook()
    event.remove(Engine, "handle_error", infra._on_handle_error)
    try:
        assert _refused("unhooked").degraded == []
    finally:
        infra.install_handle_error_hook()
