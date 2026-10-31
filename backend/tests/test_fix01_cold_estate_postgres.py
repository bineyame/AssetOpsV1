"""FIX-01 cold half (see the test docstring). Needs ASSETOPS_TEST_DATABASE_URL."""
from __future__ import annotations

from datetime import timedelta

import pytest
from test_w301_estate_index_postgres import DAY, URL, chain, cold_estate, db_now, iso, run  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


def test_cold_late_reselection_reads_200_one_row_per_finding(chain) -> None:  # noqa: F811
    """Cold half. `cold_windows` (postgres_assessment_store.py:1177) merges a job's window with every selected cold
    window inside the bridge into ONE new window and never retires the older selections, so overlapping selected cold
    windows with different revisions of one Finding are reachable in principle. The registered cold replay
    (`late-reading`) re-selects the same exact bounds, so it leaves one selected window: this records that the day
    read stays 200 with one row per Finding. The overlap itself is proven on the shared guard by the synthetic cold
    cases in test_fix01_windowed_dedupe.py (a Postgres cold overlap needs a fixture that does not exist yet)."""
    built, estate = cold_estate(chain)
    built.advance_late()
    run(built)
    day = {"from": iso(DAY), "to": iso(DAY + timedelta(days=1))}
    body = estate.ok("findings", **day)
    ids = [r["finding_id"] for r in body["rows"]]
    assert ids and len(ids) == len(set(ids))
    assert len(estate.windows(built.tenant_id, built.site_id, "cold_chain", DAY, DAY + timedelta(days=1),
                              db_now(built.engine))) == 1
