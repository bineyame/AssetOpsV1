"""W3-01 commit 2, EV half of the Run 6 Blocker 1 / Run 7 estate tests.

The W2-05b EV replay builds each case in its own fresh database, so the EV estate cannot share one database with
the cold replay of `test_w301_estate_index_postgres.py` (both fixtures are named `chain`); the EV vectors live here.
Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from test_w205b_ev_replay_postgres import URL, chain  # noqa: F401 - the W2-05b replay fixture

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w205b_ev_replay_postgres import LATE_DECISION
    from test_w206_ev_store_postgres import LATE_HI, LATE_LO, run_worker, select_exact
    from test_w301_estate_index_postgres import ESTATE_KEYS, Estate, db_now, imported_before, iso, watermark


def day_of(at: datetime) -> datetime:
    return datetime(at.year, at.month, at.day, tzinfo=timezone.utc)


def settled(chain, case: str):  # noqa: F811
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    with built.engine.connect() as c:
        first = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s"),
                          {"s": built.site_id}).scalar_one()
    imported_before(built.engine, built.tenant_id, built.site_id, day_of(first) - timedelta(days=1))
    return built, Estate(built.engine, built.tenant_id), day_of(first)


def test_ev_day_intersection_selects_exact_windows(chain) -> None:  # noqa: F811
    """A whole UTC day selects the exact EV session window; the default cutoff is later than the Site watermark
    and still reads (no EV_TIME_INVALID)."""
    built, estate, day = settled(chain, "complete")
    body = estate.ok("findings", **{"from": iso(day), "to": iso(day + timedelta(days=1))})
    windows = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1),
                             db_now(built.engine))
    (site,) = body["coverage"]["sites"]
    assert watermark(built.engine, built.site_id) < db_now(built.engine)
    assert windows and site["state"] == "CURRENT" and site["source_freshness"] == "NOT_APPLICABLE"
    assert site["selection_id"] == max(windows, key=lambda w: (w["selected_at"], w["seq"]))["selection_id"]
    assert body["status"] == "CURRENT" and body["total_count"] == len(body["rows"])
    with built.engine.connect() as c:
        supported = {str(r[0]): str(r[1]) for r in c.execute(text(
            "SELECT fr.finding_id, fr.id FROM finding_revision fr WHERE fr.site_id = :s "
            "AND fr.assessment_revision_id = ANY(CAST(:a AS uuid[])) AND fr.lifecycle = 'SUPPORTED'"),
            {"s": built.site_id, "a": [w["selection_id"] for w in windows]})}
    assert {r["finding_id"]: r["finding_revision_id"] for r in body["rows"]
            if r["lifecycle"] == "SUPPORTED"} == supported
    for row in body["rows"]:
        assert set(row["source_provenance"]) == ESTATE_KEYS and row["consequence"]["state"] == "UNPRICED"
    outside = estate.ok("findings", **{"from": iso(day + timedelta(days=3)), "to": iso(day + timedelta(days=4))})
    assert outside["coverage"]["sites"][0]["state"] == "UNKNOWN" and outside["total_count"] is None


def test_ev_multiwindow_deduplicates_and_fences(chain) -> None:  # noqa: F811
    """`late-record` plus an exact selection of `[LATE_LO, LATE_HI)`: two stored windows in one day, one canonical
    row per Finding, the assessment union of both windows in the token, a page-size invariant token and a 409 once
    a selected window changes."""
    built, estate, _ = settled(chain, "late-record")
    select_exact(built, LATE_LO, LATE_HI)
    day = day_of(LATE_LO)
    params = {"from": iso(day), "to": iso(day + timedelta(days=1))}
    windows = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1),
                             db_now(built.engine))
    assert len(windows) >= 2
    pin = iso(db_now(built.engine))
    full = estate.ok("findings", **params, known_at=pin)
    paged = estate.ok("findings", **params, known_at=pin, limit=1)
    ids = [r["finding_id"] for r in full["rows"]]
    assert len(ids) == len(set(ids))
    assert paged["selection_token"] == full["selection_token"] and paged["summary"] == full["summary"]
    default = estate.ok("findings", **params, limit=1)
    built.advance_late()
    run_worker(built)  # re-heads every intersecting exact selection
    if default["next_cursor"] is not None:
        response = estate.get("findings", **params, limit=1, cursor=default["next_cursor"])
        assert response.status_code == 409 and response.json()["detail"]["code"] == "ESTATE_BASIS_CHANGED"
    again = estate.ok("findings", **params, known_at=pin)
    # The replay's backdated late disposition moves the watermark at `pin`: rows stay, the token is fenced.
    assert again["rows"] == full["rows"] and again["selection_token"] != full["selection_token"]
    later = estate.ok("findings", **params)
    assert later["selection_token"] != full["selection_token"]


def reselect_at(chain, after_k: bool):  # noqa: F811
    """`late-record` with an exact selection of `[LATE_LO, LATE_HI)` read at `k1`, then the late phase and its
    reselection. With `after_k`, the late phase's dispositions are controlled to be decided after `k1`."""
    built, estate, _ = settled(chain, "late-record")
    day = day_of(LATE_LO)
    params = {"from": iso(day), "to": iso(day + timedelta(days=1))}
    k0 = db_now(built.engine)
    select_exact(built, LATE_LO, LATE_HI)
    k1 = db_now(built.engine)
    at_k0 = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1), k0)
    at_k1 = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1), k1)
    assert (LATE_LO, LATE_HI) not in [(w["window_start"], w["window_end"]) for w in at_k0]
    assert (LATE_LO, LATE_HI) in [(w["window_start"], w["window_end"]) for w in at_k1]
    first = estate.ok("findings", **params, known_at=iso(k1))
    built.advance_late()
    run_worker(built)
    if after_k:
        # TEST-SCOPED (Run 8 fixture ruling (b)): the replay stamps the late phase with its fixture clock (09:05),
        # backdating it before `k1`. Re-date exactly those dispositions of this tenant and Site to the DB clock,
        # after `k1` (`received_at <= decided_at` still holds), as a DB-clocked late phase would record them. The
        # append-only trigger is skipped for this one private-DB statement only (`SET LOCAL`).
        with built.engine.begin() as c:
            c.execute(text("SET LOCAL session_replication_role = replica"))
            done = c.execute(text(
                "UPDATE ingestion_disposition SET decided_at = clock_timestamp() WHERE tenant_id = :t "
                "AND site_id = :s AND decided_at = :late"),
                {"t": built.tenant_id, "s": built.site_id, "late": LATE_DECISION})
            assert done.rowcount > 0
    again = estate.ok("findings", **params, known_at=iso(k1))
    repinned = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1), k1)
    assert [(w["seq"], w["selection_id"]) for w in repinned] == [(w["seq"], w["selection_id"]) for w in at_k1]
    return built, estate, params, k1, first, again


def test_ev_cutoff_precedes_reselection_and_revision(chain) -> None:  # noqa: F811
    """Run 7 q7 at the estate level (EV), Run 8 fixture ruling (b): the late disposition is decided after `K`, so
    the repeat read at `K` returns the identical full coverage (watermark included), rows, selected IDs and
    `estate-selection/2` token after reselection, and a later cutoff changes the token."""
    built, estate, params, k1, first, again = reselect_at(chain, True)
    assert watermark(built.engine, built.site_id) > k1  # the late decision is after K, never backdated
    assert again["status"] == first["status"] == "HISTORICAL"
    assert again["coverage"] == first["coverage"] and again["rows"] == first["rows"]
    assert again["summary"] == first["summary"] and again["selection_token"] == first["selection_token"]
    assert estate.ok("findings", **params)["selection_token"] != first["selection_token"]


def test_ev_backdated_disposition_limitation_fences(chain) -> None:  # noqa: F811
    """LIMITATION, not the q7 equality proof: the replay's fixture clock backdates the late disposition (09:05)
    before `K`, moving the Site evidence watermark at `K`. The token must then change (the fence holds)."""
    built, _, _, k1, first, again = reselect_at(chain, False)
    assert watermark(built.engine, built.site_id) <= k1
    assert again["rows"] == first["rows"]
    assert again["coverage"]["sites"][0]["committed_watermark"] != first["coverage"]["sites"][0][
        "committed_watermark"]
    assert again["selection_token"] != first["selection_token"]
