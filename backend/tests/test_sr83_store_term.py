"""D-SR.83b (no database): `StoredRoute.term` joins the stored route's watermark as `|s:{term()}` at lookup (a) and at
the recheck (c): a changed term misses, and a term that changes during the compose is a `race`, never stored."""
from __future__ import annotations

from uuid import uuid4

from assetops_backend.chain.response_store import HEADER, ResponseStore, StoredRoute


class Snap:
    def watermark(self, tenant, sites):
        return "w1"

    def sites(self, tenant):
        return []

    def lookup(self, *a):
        return None


class Rows:
    def __init__(self) -> None:
        self.inserted: list = []

    def read(self, work):
        return work(Snap())

    def insert(self, *a, **k):
        self.inserted.append(a)
        return []

    def prune(self):
        return 0

    def dispose(self):
        pass


def _store(rows):
    return ResponseStore(rows, lambda: "v1")


def test_the_term_is_appended_to_the_watermark_and_a_changed_term_changes_it() -> None:
    term = ["a"]
    req = StoredRoute("/r", uuid4(), {}, sites=(), term=lambda: term[0])
    store = _store(Rows())
    first = store.watermark(req)
    assert first == "w1|s:a"
    term[0] = "b"
    assert store.watermark(req) == "w1|s:b" != first
    assert _store(Rows()).watermark(StoredRoute("/r", uuid4(), {}, sites=())) == "w1"  # no term, unchanged


def test_a_term_that_changes_during_the_compose_is_a_race_and_is_not_stored() -> None:
    term = ["a"]
    rows = Rows()
    req = StoredRoute("/r", uuid4(), {}, sites=(), term=lambda: term[0])

    def compose():
        term[0] = "b"  # the schedule flips mid-compose
        return {"/r": {"x": 1}}

    response = _store(rows).serve(req, compose)
    assert response.headers[HEADER] == "race"
    assert rows.inserted == []
