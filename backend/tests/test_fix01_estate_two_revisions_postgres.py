"""FIX-01: one EV Finding revised per assessed window, two overlapping selected windows in one UTC day.

The replay's worker window is [08:00, 09:05) (rev 1); an exact selection of E = [08:00, 09:00) (the shape any earlier
job's window leaves) refreshes the basis (rev 2). The estate day reads must be 200, one row at the head revision, the
Site sets stay unions over both windows and the Finding link opens the winning window."""
from __future__ import annotations

from datetime import timedelta
from urllib.parse import unquote

import pytest
from test_w205b_ev_replay_postgres import URL, chain  # noqa: F401 - the W2-05b replay fixture

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w206_ev_store_postgres import select_exact
    from test_w301_estate_index_ev_postgres import day_of, settled
    from test_w301_estate_index_postgres import db_now, iso
    from test_w302_evidence_scope_snapshot_postgres import Evidence


def _two_windows(chain):  # noqa: F811
    built, estate, day = settled(chain, "interrupted")
    with built.engine.connect() as c:
        lo, hi = c.execute(text("SELECT min(window_start), max(window_end) FROM analytic_run_selection "
                                "WHERE site_id = :s"), {"s": built.site_id}).one()
    e_hi = hi - timedelta(minutes=5)
    select_exact(built, lo, e_hi)
    with built.engine.connect() as c:
        revs = c.execute(text(
            "SELECT finding_id, id, revision_no FROM finding_revision WHERE site_id = :s AND domain <> 'mini_grid' "
            "ORDER BY revision_no"), {"s": built.site_id}).all()
        sel = c.execute(text("SELECT window_start, window_end FROM analytic_run_selection WHERE site_id = :s "
                             "ORDER BY seq"), {"s": built.site_id}).all()
    return built, estate, day, (lo, e_hi), revs, sel


def test_ev_two_selected_windows_two_revisions_reads_200(chain) -> None:  # noqa: F811
    built, estate, day, exact, revs, sel = _two_windows(chain)
    assert len({r[0] for r in revs}) == 1 and [r[2] for r in revs] == [1, 2], revs  # one Finding, two revisions
    assert len(set(sel)) == 2, sel  # two different selected windows, not one window twice
    params = {"from": iso(day), "to": iso(day + timedelta(days=1))}
    findings = estate.ok("findings", **params)
    assert [r["finding_id"] for r in findings["rows"]] == [str(revs[0][0])]
    row = findings["rows"][0]
    assert row["finding_revision_id"] == str(revs[1][1])  # the head (revision_no 2) wins, not the older window's
    evidence = Evidence(built.engine, built.tenant_id).ok(**params, limit=100)  # the second route that raised
    assert evidence["status"] == "CURRENT" and evidence["rows"]
    windows = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1),
                             db_now(built.engine))
    assert len(windows) == 2  # the Site-level sets stay unions over both selected windows
    assert len({w["selection_id"] for w in windows}) == 2
    # the Finding link opens the winning window (rev 2 = the exact [lo, e_hi) selection), not null
    href = unquote(row["links"]["finding"] or "")
    stamp = "%Y-%m-%dT%H:%M:%S"
    assert exact[0].strftime(stamp) in href and exact[1].strftime(stamp) in href, href
    assert (exact[1] + timedelta(minutes=5)).strftime(stamp) not in href, href
    # 6 Oct is the only day with rows; the day before is empty and still 200
    assert estate.ok("findings", **{"from": iso(day - timedelta(days=1)), "to": iso(day)})["rows"] == []

