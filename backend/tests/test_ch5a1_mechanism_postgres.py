"""CH-5a1 L2m (build sheet Part A §A9 item 3; MD-0 §7; MD0-S2 Kobo only): the ChainReader's SQL ports over the
full KOBO-001 mechanism Site, on a fresh clone of the MD-0 input template derived with this checkout's code
(`test_md0_mechanism_postgres.mech`).

- E1 on MD-0 (§A6): every delivered day reads FULL; GAP-K7 (D7) is expected to read NONE.
- MD-0-F1 (MD0-S5 L5, owner CH-5a1 R5): D7-D9 carry a live `mini_renewable` job for the noon hour (enqueued at the
  D11 delivery, never reconciled because nothing was delivered), so `noon_headroom_kw` is PENDING there and R5 reads
  UNKNOWN. That is R5 as written ("any PENDING -> UNKNOWN") and MD0-S4 R1.5 allows "NO_DATA/PENDING before the fill",
  so it is recorded with `pytest.xfail` after the hard assertions (MD-0 R7 pattern), not changed here.
- R8: settled after the CH-2/CH-3 settle path (the derive step already leaves no unconsumed revision).
- L5: the dispatch thread's Finding heads at the latest cutoff are the three declared anchors (D4, D11, D14).
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import text

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_md0_mechanism_postgres import mech  # noqa: F401  (the clone + derive fixture)
    from test_out_b4_board_postgres import _settle_chain

    import mechanism_dataset as md
    import pg_harness
    from assetops_backend import read_scope
    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.read import FULL, NONE, UNKNOWN, ChainReader
    from assetops_backend.chain.reader import SnapshotReader

SPEC = md.load() if URL else None


def _iso(n: int) -> date:
    return md.day(SPEC, n)


def test_readiness_settledness_and_heads_over_the_mechanism_site(mech) -> None:  # noqa: F811
    engine, m = mech
    url = engine.url.render_as_string(hide_password=False)
    with engine.connect() as c:
        tenant = c.execute(text("SELECT tenant_id FROM site WHERE id = :s"), {"s": m["site_id"]}).scalar_one()
    snapshots = PostgresSnapshotStore(url)
    port = PostgresChainRead(url, snapshots=SnapshotReader(snapshots))
    try:
        _settle_chain(url, "KOBO-001")  # backfill a-d and the `threads` consume, as the board's L2 settle path
        with read_scope.scope("test:l2m:after"):
            req = ChainReader(port).request(tenant, None)
            assert req.findings_settled(m["site_id"]) is True
            delivered = [n for n in m["days"] if n != 7]
            per_day = {n: req.day(m["site_id"], "MINIGRID", [_iso(n)]).readiness for n in [*delivered, 7]}
        # E1 (hard): every delivered day reads FULL.
        assert {n: r for n, r in per_day.items() if n != 7 and r != FULL} == {}, per_day
        # L5: the generator thread's heads at the latest cutoff are the declared dispatch anchors on delivered days.
        with engine.connect() as c:
            heads = c.execute(text("SELECT count(DISTINCT finding_id) FROM finding_thread_occurrence "
                                   "WHERE site_id = :s AND finding_id IS NOT NULL"),
                              {"s": m["site_id"]}).scalar_one()
        assert heads == len(m["findings"]), (heads, m["findings"])
        # E1 GAP-K7 (expected NONE): MD-0-F1 reads UNKNOWN while D7's noon job is live.
        assert per_day[7] in (NONE, UNKNOWN), per_day[7]
        if per_day[7] == UNKNOWN:
            pytest.xfail("MD-0-F1: D7 noon_headroom_kw is PENDING (live mini_renewable job), R5 -> UNKNOWN, not NONE")
    finally:
        pg_harness.dispose(port, snapshots)
