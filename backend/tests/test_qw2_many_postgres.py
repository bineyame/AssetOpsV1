"""QW-2 (design proposal §14b): each `*_many` estate read equals the single-Site method for every Site of the W3-03
four-Site three-domain fixture, plus a Site outside the scope (None), on one snapshot. Needs
ASSETOPS_TEST_DATABASE_URL."""
from __future__ import annotations

from datetime import timedelta

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: F401 - the replay factories
    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4 mini-grid fixtures
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w303_portfolio_fixture_postgres import CODES, DAY, WINDOW_TO, build_portfolio_fixture

    from assetops_backend.estate.portfolio import EstatePortfolioService

OUTSIDE = "NOPE-001"


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "3e" * 32)


def test_many_equals_single_for_every_site_and_none_outside(request, monkeypatch, capsys) -> None:
    fx = build_portfolio_fixture(request, monkeypatch, capsys)
    reader = evidence_read(fx.engine)
    snapshots = []
    real = reader.read
    reader.read = lambda work: snapshots.append(1) or real(work)
    svc = EstatePortfolioService(reader)
    t, k = fx.tenant_id, fx.frozen
    codes = [*CODES, OUTSIDE]
    lo, hi = DAY, DAY + timedelta(days=1)
    work_lo = WINDOW_TO - timedelta(days=31)
    week_lo = WINDOW_TO - timedelta(days=7)

    windows = svc.site_selected_windows_many(t, codes, lo, WINDOW_TO, k)
    ready = svc.site_readiness_many(t, {c: (lo, hi) if c == "KOBO-001" else (week_lo, WINDOW_TO) for c in codes}, k)
    rows = svc.site_work_rows_many(t, {c: (lo, hi, work_lo, WINDOW_TO) for c in codes}, k)
    assert len(snapshots) == 3  # one snapshot per batched call
    for c in codes:
        assert windows[c] == svc.site_selected_windows(t, c, lo, WINDOW_TO, k), c
        a, b = (lo, hi) if c == "KOBO-001" else (week_lo, WINDOW_TO)
        assert ready[c] == svc.site_readiness(t, c, a, b, k), c
        assert rows[c] == svc.site_work_rows(t, c, lo, hi, work_lo, WINDOW_TO, k), c
    assert windows[OUTSIDE] is None and ready[OUTSIDE] is None and rows[OUTSIDE] is None
    # non-vacuous: the fixture gives real values (a cold window, readiness states, Kobo Finding rows)
    assert any(windows[c] for c in CODES) and all(ready[c] is not None for c in CODES)
    assert rows["KOBO-001"] is not None and rows["KOBO-001"]["findings"]

    before = len(snapshots)
    shared = svc.read_snapshot(lambda snap: (
        svc.site_selected_windows_many(t, codes, lo, WINDOW_TO, k, snap=snap),
        svc.site_readiness_many(t, {c: (lo, hi) for c in codes}, k, snap=snap),
        svc.site_work_rows_many(t, {c: (lo, hi, work_lo, WINDOW_TO) for c in codes}, k, snap=snap)))
    assert len(snapshots) == before + 1  # the three batches on the caller's one snapshot
    assert shared[0] == windows and shared[2] == rows
    assert shared[1] == {c: svc.site_readiness(t, c, lo, hi, k) for c in codes}
