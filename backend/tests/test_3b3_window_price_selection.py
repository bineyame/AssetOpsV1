"""3B3 (P2): `financials.composition.build_window_price_selection` disposes the one store it builds."""

from __future__ import annotations

from assetops_backend.financials import composition


def test_dispose_disposes_every_store_built(monkeypatch):
    built = []

    class FakeStore:
        def __init__(self, url):
            self.url, self.disposed = url, 0
            built.append(self)

        def dispose(self):
            self.disposed += 1

    monkeypatch.setattr(composition, "PostgresAssumptionStore", FakeStore)
    selection = composition.build_window_price_selection("postgresql://x")
    assert len(built) == 1
    selection.dispose()
    assert [s.disposed for s in built] == [1]
