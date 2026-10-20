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
    from test_w206_ev_store_postgres import LATE_HI, LATE_LO, run_worker, select_exact
    from test_w301_estate_index_postgres import ESTATE_KEYS, Estate, db_now, imported_before, iso, watermark


def day_of(at: datetime) -> datetime:
    return datetime(at.year, at.month, at.day, tzinfo=timezone.utc)


def without_watermark(body: dict) -> list[dict]:
    return [{k: v for k, v in x.items() if k != "committed_watermark"} for x in body["coverage"]["sites"]]


def assert_pinned(again: dict, first: dict) -> None:
    """The same explicit cutoff keeps its rows, selected IDs and coverage. FIXTURE LIMIT: the EV replay stamps
    `ingestion_disposition.decided_at` with its fixture clock (2026-10-06), so late evidence written after the
    cutoff is backdated before it and moves the Site evidence watermark (and with it the token); the cold replay
    is DB-clocked and proves the whole-token equality in `test_w301_estate_index_postgres.py`."""
    assert again["rows"] == first["rows"] and without_watermark(again) == without_watermark(first)
    if again["selection_token"] != first["selection_token"]:
        assert again["coverage"]["sites"][0]["committed_watermark"] != first["coverage"]["sites"][0][
            "committed_watermark"]


def settled(chain, case: str):  # noqa: F811
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    with built.engine.connect() as c:
        first = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s"),
                          {"s": built.site_id}).scalar_one()
    imported_before(built.engine, built.site_id, day_of(first) - timedelta(days=1))
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
    assert_pinned(again, full)
    later = estate.ok("findings", **params)
    assert later["selection_token"] != full["selection_token"]


def test_ev_cutoff_precedes_reselection_and_revision(chain) -> None:  # noqa: F811
    """Run 7 q7 at the estate level (EV): the selection written after the watermark is visible once its
    `selected_at` is within the requested cutoff, and an explicit earlier cutoff keeps its seq, rows and token."""
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
    again = estate.ok("findings", **params, known_at=iso(k1))
    repinned = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1), k1)
    assert [(w["seq"], w["selection_id"]) for w in repinned] == [(w["seq"], w["selection_id"]) for w in at_k1]
    assert again["status"] == first["status"] == "HISTORICAL"
    assert_pinned(again, first)
