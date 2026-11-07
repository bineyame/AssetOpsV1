"""MB-1a L2 (FUEL-1 MB-1-R §2.5): the mill's verdict on `_SITE_ACTIONS`, `opportunity_actions` and the claim, on real
rows built from the CH-9b fixtures (the W4-02 MINIGRID Site, CH-4's seeded opportunity).

Sequence: threads step b; create, complete, link and freeze the mill (`_frozen`); threads steps b, c (the Action
link); later snapshots and `evaluate_domain_plan` -> VERIFIED; `run_lifecycle`. Then:
- `PostgresChainRead.site_threads` carries the mill row with `outcome` VERIFIED and its stored `recorded_at`;
- one second before that `recorded_at`, `opportunity_actions` reads the outcome as not judged (None);
- over the occurrence's window it gives one item (DOMAIN_VERDICT ref);
- `estate_count_claims` through a `ChainReader` on this database counts it once (`verified_actions` 1).
"""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_ch9b1_opportunity_actions_postgres import _lifecycle, _threads, mill  # noqa: F401
    from test_ch9b3_mill_verdict_postgres import _after, _close, _frozen, _later
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.chain import claims as CL
    from assetops_backend.chain import site_chain
    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead
    from assetops_backend.chain.read import ChainReader


def test_the_mill_verdict_reaches_the_site_actions_and_the_claim(mill, monkeypatch) -> None:
    _threads(mill, ("b",))
    svc, clock, aid, eff, tz = _frozen(mill, "mb1")
    read = PostgresChainRead(URL)
    try:
        _threads(mill, ("b", "c"))
        _later(mill, eff, "11.5")
        clock.at = _after(eff, tz, 5)
        assert svc.evaluate_domain_plan(mill.t, mill.s, aid)["state"] == "VERIFIED"
        _lifecycle(mill)
        with mill.engine.connect() as c:
            recorded = c.execute(text("SELECT recorded_at FROM verification_outcome WHERE domain_action_id = :a"),
                                 {"a": aid}).scalar_one()
            code = c.execute(text("SELECT site_code FROM site WHERE id = :s"), {"s": mill.s}).scalar_one()

        rows = read.site_threads(mill.t, mill.s, None)
        (row,) = [a for a in rows["actions"] if a["action_id"] == aid]
        assert row["kind"] == "DOMAIN_INTENT" and row["thread_id"] is not None  # S-c: the link is reachable
        assert row["outcome"] == "VERIFIED" and row["outcome_recorded_at"] == recorded
        assert all(a["outcome"] is None and a["outcome_recorded_at"] is None
                   for a in rows["actions"] if a["kind"] == "MINI_TRIAL")

        occ = next(o for o in rows["occurrences"] if o["thread_id"] == row["thread_id"] and o["opportunity_id"])
        lo, hi = occ["episode_start"], row["accepted_at"] + timedelta(seconds=1)
        (item,) = site_chain.opportunity_actions(rows, site=code, tz=tz, cutoff=None, lo=lo, hi=hi)
        assert item["action_id"] == aid and item["outcome"] == "VERIFIED" and item["ref"]["kind"] == "DOMAIN_VERDICT"
        (early,) = site_chain.opportunity_actions(rows, site=code, tz=tz, cutoff=recorded - timedelta(seconds=1),
                                                  lo=lo, hi=hi)
        assert early["outcome"] is None

        monkeypatch.setattr(CL, "claim_days", lambda req, site, lo, hi: None)  # the day grades are not under test
        site = SimpleNamespace(site_id=mill.s, site_code=code, domain="mini_grid", timezone=tz, tenant_id=mill.t)
        out = CL.estate_count_claims(ChainReader(read).request(mill.t, None), [site], lo, hi, [])
        assert out.threads[code]["verified_actions"] == 1
        assert out.claims[CL.VERIFIED_RESULTS].value == out.threads[code]["verified"] + 1
    finally:
        pg_harness.dispose(read)
        _close(mill)
