"""FIX-S4-DOMAIN: `PostgresFindingStore.episodes` filters by domain and analytic, defaulting to the mini
dispatch matcher's (mini_grid / dispatch). Pure: the store's read runs against a recording connection."""

from __future__ import annotations

from uuid import uuid4

from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore


class _Rows:
    def all(self) -> list:
        return []


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def execute(self, statement, params):
        self.calls.append((str(statement), params))
        return _Rows()


def _episodes(*args) -> tuple[str, dict]:
    store, conn = PostgresFindingStore(None), _Recorder()
    store._read = lambda work: work(conn)  # no engine: the query and its parameters only
    assert store.episodes(*args) == []
    [(sql, params)] = conn.calls
    return sql, params


def test_episodes_defaults_to_the_mini_dispatch_domain_and_analytic() -> None:
    sql, params = _episodes(uuid4(), uuid4())
    assert "f.domain = :d AND f.analytic_id = :a" in sql
    assert params["d"] == "mini_grid" and params["a"] == "dispatch"


def test_episodes_passes_an_explicit_domain_and_analytic() -> None:
    _, params = _episodes(uuid4(), uuid4(), "cold_chain", "cold-excursion")
    assert params["d"] == "cold_chain" and params["a"] == "cold-excursion"
