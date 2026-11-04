"""CH-5a1 L0: the per-request read scope (CH5a-R R1): ledger, memo, deep freeze."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from uuid import uuid4

import pytest

from assetops_backend import perf, read_scope as rs


@dataclass(frozen=True)
class Snap:
    head: dict
    jobs: list


def test_memo_hits_on_equal_keys_and_counts_one_execution():
    calls = []

    def fn(a, b):
        calls.append((a, b))
        return {"v": [a, b]}
    with rs.scope("t") as sc:
        first = rs.memo("x", fn, 1, 2)
        assert rs.memo("x", fn, 1, 2) is first
        rs.memo("x", fn, 1, 3)
        assert calls == [(1, 2), (1, 3)]
        assert sc.max_per_key() == 1 and sc.names() == {"x": 2} and sc.hits == {"x": 1}


def test_a_raising_call_is_not_memoised():
    n = {"c": 0}

    def boom():
        n["c"] += 1
        raise RuntimeError("no")
    with rs.scope("t"):
        for _ in range(2):
            with pytest.raises(RuntimeError):
                rs.memo("y", boom)
    assert n["c"] == 2


def test_results_are_deep_frozen():
    with rs.scope("t"):
        out = rs.memo("z", lambda: {"a": [1, {"b": 2}]})
        assert isinstance(out, MappingProxyType) and out["a"][1]["b"] == 2
        with pytest.raises(TypeError):
            out["a"] = 1  # type: ignore[index]
        with pytest.raises(TypeError):
            out["a"][1]["b"] = 3  # type: ignore[index]
        snap = rs.memo("w", lambda: Snap({"seq": 1}, [{"id": 1}]))
        assert isinstance(snap.head, MappingProxyType) and isinstance(snap.jobs, tuple)
        assert rs.thaw(out) == {"a": [1, {"b": 2}]}


def test_outside_a_scope_there_is_no_memo():
    calls = []
    assert rs.current() is None
    rs.memo("x", lambda: calls.append(1) or [1])
    out = rs.memo("x", lambda: calls.append(1) or [1])
    assert calls == [1, 1] and out == [1]   # mutable, not frozen, outside a scope
    rs.record("x", (1,), 1.0)               # no-op


def test_explicit_key_overrides_the_arguments():
    with rs.scope("t") as sc:
        rs.memo("k", lambda: 1, key=("a",))
        rs.memo("k", lambda: 2, key=("a",))
        assert sc.names() == {"k": 1}


def test_ledger_counts_repeats_and_perf_route_enters_one_scope():
    with perf.route("board"):
        sc = rs.current()
        assert sc is not None
        rs.record("dispatch", ("t", "s"), 1.0)
        rs.record("dispatch", ("t", "s"), 1.0)
        with rs.scope("inner") as inner:
            assert inner is sc                # nested: one request, one scope
        assert sc.repeated() == [("dispatch", ("t", "s"), 2)] and sc.max_per_key() == 2
    assert rs.current() is None


def test_window_memo_excludes_knowledge_at_only_without_a_cutoff():
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_inputs import EvidenceQuery
    from assetops_backend.analytics.dispatch_read import day_window
    store = PostgresAssessmentStore.__new__(PostgresAssessmentStore)
    calls = []

    def read(c, q, a, b, cutoff=None, all_jobs=False):
        calls.append((q.knowledge_at, cutoff))
        return ("snap", len(calls))
    store._window_read = read  # type: ignore[method-assign]
    t, s = uuid4(), uuid4()
    k1 = datetime(2026, 11, 1, tzinfo=timezone.utc)

    def q(k):
        return EvidenceQuery(t, s, "dispatch", day_window(k1.date()), k)

    def basis(r):
        return None, ""
    with rs.scope("t"):
        a = store._window(None, q(k1), "dispatch", basis)
        b = store._window(None, q(k1 + timedelta(minutes=1)), "dispatch", basis)   # live: first read wins
        assert a is b and len(calls) == 1
        store._window(None, q(k1), "dispatch", basis, cutoff=k1)
        store._window(None, q(k1 + timedelta(minutes=1)), "dispatch", basis, cutoff=k1)  # cutoff: keyed
        store._window(None, q(k1), "dispatch", basis, cutoff=k1)
        assert len(calls) == 3
