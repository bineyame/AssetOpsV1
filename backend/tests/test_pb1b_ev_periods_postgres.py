"""PB-1b (D-E5.31): EV analysed periods inside a requested window, default Site selection only.

Rule (`.agent/architect-answer-non-kobo-sites-2026-11-10.md` D-E5.31, card PB-1b): (i) a stored selection equal to
the window is unchanged (EV's default selection is exact-window); (ii) otherwise the selected analysed periods lying
wholly inside the window are listed, two stored windows sharing a start listing only the widest, and the snapshot
reads the most recent one with an open (SUPPORTED) Finding, or else the most recent one; (iii) none inside is
today's empty selection. Pinned mode is unchanged. E4: EV source provenance is judged on the analysed period read,
never over the union of the window.

Over the registered W2-05b replays and the production EV worker. The extra periods of the week case are further
`analytic_run_selection` rows (append-only, inserted only) re-selecting the same stored run on later days, so they
carry no Finding of their own. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest

from test_w205b_ev_replay_postgres import URL, chain  # noqa: F401 - the W2-05b replay fixture

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w206_ev_store_postgres import LATE_HI, LATE_LO, run_worker, select_exact
    from test_w207_ev_site_reads_postgres import client, get

    from assetops_backend.analytics import ev
    from assetops_backend.analytics.adapters.postgres_assessment_store import EvReadService
    from assetops_backend.evidence.composition import build_link_rows_reader

CODE = "EV-LAB-001"
EV = "ev-session/1"  # ev.SESSION_ANALYTIC


@contextmanager
def snapshot(built):
    with built.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c


def settled(chain, case: str):  # noqa: F811
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    return built


def clocks(built) -> tuple[datetime, datetime]:
    """(the Site's committed evidence watermark, the database clock now)."""
    with built.engine.connect() as c:
        return (c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                          {"s": built.site_id}).scalar_one(),
                c.execute(text("SELECT clock_timestamp()")).scalar_one())


def windows(built) -> list[tuple[datetime, datetime]]:
    with built.engine.connect() as c:
        return [(r[0], r[1]) for r in c.execute(text(
            "SELECT DISTINCT window_start, window_end FROM analytic_run_selection WHERE site_id = :s "
            "AND analytic_id = :a ORDER BY window_start, window_end"), {"s": built.site_id, "a": EV}).all()]


def widest(ws: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Expected listing: no period lying wholly inside another (shared start or nested)."""
    return [p for p in sorted(set(ws)) if not any(q != p and q[0] <= p[0] and p[1] <= q[1] for q in ws)]


def day_of(at: datetime) -> tuple[datetime, datetime]:
    d = datetime(at.year, at.month, at.day, tzinfo=timezone.utc)
    return d, d + timedelta(days=1)


def reselect_later_days(built, days: tuple[int, ...]) -> list[tuple[datetime, datetime]]:
    """Insert selections of the latest stored EV run shifted by whole days: further analysed periods, no Finding."""
    with built.engine.begin() as c:
        h = c.execute(text(
            "SELECT tenant_id, site_id, analytic_id, window_start, window_end, run_id FROM analytic_run_selection "
            "WHERE site_id = :s AND analytic_id = :a ORDER BY seq DESC LIMIT 1"), {"s": built.site_id, "a": EV}).one()
        for d in days:
            c.execute(text(
                "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, "
                "run_id, job_id, selected_at) VALUES (:t, :s, :a, :lo, :hi, :r, NULL, clock_timestamp())"),
                {"t": h[0], "s": h[1], "a": h[2], "lo": h[3] + timedelta(days=d), "hi": h[4] + timedelta(days=d),
                 "r": h[5]})
    return [(h[3] + timedelta(days=d), h[4] + timedelta(days=d)) for d in days]


def open_finding_anchors(built) -> list[datetime]:
    with built.engine.connect() as c:
        return [r[0] for r in c.execute(text(
            "SELECT f.anchor_start FROM finding f WHERE f.site_id = :s AND f.domain = 'ev_charging' AND "
            "(SELECT r.lifecycle FROM finding_revision r WHERE r.finding_id = f.id ORDER BY r.revision_no DESC "
            "LIMIT 1) = 'SUPPORTED'"), {"s": built.site_id}).all()]


def service(built) -> EvReadService:
    return EvReadService(engine=built.engine, link_rows=build_link_rows_reader())


def test_day_window_over_one_period(chain) -> None:  # noqa: F811
    built = settled(chain, "complete")
    stored = windows(built)
    assert len(stored) == 1, stored
    lo, hi = stored[0]
    wm, _ = clocks(built)
    svc, t, s = service(built), built.tenant_id, built.site_id
    day = day_of(lo)
    with snapshot(built) as c:
        whole = svc._snapshot(c, t, s, CODE, *day, wm)
        exact = svc._snapshot(c, t, s, CODE, lo, hi, wm)
    assert day[0] <= lo and hi <= day[1]
    assert whole["analysed_periods"] == [(lo, hi)] and whole["shown_period"] == (lo, hi)
    assert (whole["lo"], whole["hi"]) == (lo, hi)  # the status bar and Needs attention read the analysed period
    assert whole["selected"] is not None and whole["selected"]["revision_id"] == exact["selected"]["revision_id"]
    assert whole["state"] == exact["state"]
    # (i) a stored selection equal to the window is unchanged: nothing is substituted or listed.
    assert exact["analysed_periods"] == [] and exact["shown_period"] is None and (exact["lo"], exact["hi"]) == (lo, hi)


def test_week_over_several_periods_open_finding_wins(chain) -> None:  # noqa: F811
    built = settled(chain, "interrupted")
    stored = windows(built)
    assert len(stored) == 1, stored
    failure = stored[0]
    anchors = open_finding_anchors(built)
    assert anchors and all(failure[0] <= a < failure[1] for a in anchors), anchors
    later = reselect_later_days(built, (1, 2, 3))
    wm, _ = clocks(built)
    svc, t, s = service(built), built.tenant_id, built.site_id
    week = (day_of(failure[0])[0] - timedelta(days=1), day_of(failure[0])[0] + timedelta(days=6))
    with snapshot(built) as c:
        whole = svc._snapshot(c, t, s, CODE, *week, wm)
        quiet = svc._snapshot(c, t, s, CODE, later[0][0] - timedelta(hours=1), week[1], wm)
    assert whole["analysed_periods"] == [failure, *later]
    assert whole["shown_period"] == failure and (whole["lo"], whole["hi"]) == failure  # the open Finding wins
    assert whole["selected"] is not None
    # With no open Finding among the periods inside, the most recent one is shown.
    assert quiet["analysed_periods"] == later and quiet["shown_period"] == later[-1]
    assert (quiet["lo"], quiet["hi"]) == later[-1] and quiet["selected"] is not None


def test_shared_start_lists_only_the_widest(chain) -> None:  # noqa: F811
    built = settled(chain, "late-record")
    select_exact(built, LATE_LO, LATE_HI)
    stored = windows(built)
    day = day_of(LATE_LO)
    inside = [w for w in stored if day[0] <= w[0] and w[1] <= day[1]]
    starts = [w[0] for w in inside]
    assert len(starts) > len(set(starts)), inside  # non-vacuous: two stored windows share a start
    wm, _ = clocks(built)
    svc, t, s = service(built), built.tenant_id, built.site_id
    with snapshot(built) as c:
        whole = svc._snapshot(c, t, s, CODE, *day, wm)
    assert whole["analysed_periods"] == widest(inside)
    assert (LATE_LO, LATE_HI) not in whole["analysed_periods"]  # the narrower 08:00 window is not listed
    assert whole["shown_period"] in whole["analysed_periods"] and whole["selected"] is not None


def test_nested_window_is_never_listed_or_shown(chain) -> None:  # noqa: F811
    """PB-1a review L1: a stored window wholly inside another is dropped, so the shown period is never a nested
    duplicate (and never reads UNKNOWN for that reason)."""
    built = settled(chain, "complete")
    lo, hi = windows(built)[0]
    nested = (lo + timedelta(minutes=10), hi - timedelta(minutes=10))
    select_exact(built, *nested)  # the latest selection, so "most recent by seq" would not save the outer one
    assert nested in windows(built)  # non-vacuous: the nested window is stored and selected
    wm, _ = clocks(built)
    svc, t, s = service(built), built.tenant_id, built.site_id
    with snapshot(built) as c:
        whole = svc._snapshot(c, t, s, CODE, *day_of(lo), wm)
    assert whole["analysed_periods"] == [(lo, hi)] and whole["shown_period"] == (lo, hi)
    assert whole["selected"] is not None and whole["state"] != "UNKNOWN"


def test_widest_periods_unit() -> None:
    from assetops_backend.analytics.adapters.postgres_assessment_store import widest_periods

    def at(h: int, m: int = 0) -> datetime:
        return datetime(2026, 11, 3, h, m, tzinfo=timezone.utc)

    got = widest_periods([(at(8), at(9)), (at(8), at(9, 5)), (at(8, 10), at(8, 20)), (at(10), at(11)),
                          (at(10), at(11)), (at(10, 30), at(12))])
    assert got == [(at(8), at(9, 5)), (at(10), at(11)), (at(10, 30), at(12))]  # overlapping, not nested: both kept


def test_window_with_no_period_inside(chain) -> None:  # noqa: F811
    built = settled(chain, "complete")
    lo, hi = windows(built)[0]
    wm, _ = clocks(built)
    svc, t, s = service(built), built.tenant_id, built.site_id
    empty = (day_of(lo)[0] + timedelta(days=10), day_of(lo)[0] + timedelta(days=17))
    straddle = (lo + timedelta(minutes=5), hi + timedelta(hours=1))  # overlaps the period but does not hold it
    with snapshot(built) as c:
        none = svc._snapshot(c, t, s, CODE, *empty, wm)
        partial = svc._snapshot(c, t, s, CODE, *straddle, wm)
    for snap, window in ((none, empty), (partial, straddle)):
        assert snap["analysed_periods"] == [] and snap["shown_period"] is None
        assert snap["selected"] is None and snap["state"] == "UNKNOWN" and (snap["lo"], snap["hi"]) == window


def test_pinned_mode_unchanged(chain) -> None:  # noqa: F811
    built = settled(chain, "interrupted")
    failure = windows(built)[0]
    later = reselect_later_days(built, (1, 2))
    wm, k = clocks(built)
    svc, t, s = service(built), built.tenant_id, built.site_id
    week = (day_of(failure[0])[0], day_of(failure[0])[0] + timedelta(days=7))
    with snapshot(built) as c:
        pinned = svc.estate_snapshots_on(c, t, s, CODE, *week, wm, k)
    assert [(p["lo"], p["hi"]) for p in pinned] == [failure, *later]  # one exact snapshot per stored window
    for p in pinned:
        assert p["selected"] is not None and p["selection_seqs"]
        assert p["analysed_periods"] == [] and p["shown_period"] is None


def test_provenance_judged_per_period_not_over_the_union(chain, monkeypatch) -> None:  # noqa: F811
    """E4: every story day is its own registered run, so the S4-05 classifier calls a multi-period union MIXED.
    The fake classifier below answers MIXED for any window holding more than one analysed period and assessable
    for one period; the read must judge only the period it shows."""
    built = settled(chain, "interrupted")
    failure = windows(built)[0]
    later = reselect_later_days(built, (1, 2))
    periods = [failure, *later]
    judged: list[tuple[datetime, datetime]] = []

    def classify(self, c, t, s, lo, hi, known):
        judged.append((lo, hi))
        held = [p for p in periods if lo <= p[0] and p[1] <= hi]
        if len(held) <= 1:
            return None
        return {"classification": "MIXED", "evidence_ids": [], "source_ids": [],
                "reasons": [{"code": "MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS", "accepted_evidence_ids": []}]}

    monkeypatch.setattr(EvReadService, "_unassessable", classify)
    wm, _ = clocks(built)
    week = (day_of(failure[0])[0], day_of(failure[0])[0] + timedelta(days=7))
    svc, t, s = service(built), built.tenant_id, built.site_id
    with snapshot(built) as c:
        snap = svc._snapshot(c, t, s, CODE, *week, wm)
        body = svc._envelope(c, snap)
    assert snap["unassessable"] is None and snap["note"] != ev.SOURCE_UNASSESSABLE
    assert ev.SOURCE_UNASSESSABLE not in body["limitations"]
    assert week not in judged  # never judged over the union
    # The Site overview over the same week: no unassessable note in its envelope or Needs attention.
    monkeypatch.setattr(EvReadService, "_unassessable", classify)
    c = client(built)
    q = f"from={week[0].isoformat().replace('+00:00', 'Z')}&to={week[1].isoformat().replace('+00:00', 'Z')}"
    overview = get(c, f"overview?{q}")
    assert ev.SOURCE_UNASSESSABLE not in overview["limitations"]
    assert ev.SOURCE_UNASSESSABLE not in str(overview["needs_attention"])
    assert len(overview["analysed_periods"]) == 3 and overview["status"]["state"] != "UNKNOWN"


def test_site_reads_carry_analysed_periods(chain) -> None:  # noqa: F811
    built = settled(chain, "complete")
    lo, hi = windows(built)[0]
    day = day_of(lo)
    c = client(built)

    def z(at: datetime) -> str:
        return at.isoformat().replace("+00:00", "Z")

    reads = {name: get(c, f"{path}?from={z(day[0])}&to={z(day[1])}") for name, path in (
        ("overview", "overview"), ("evidence", "evidence"), ("analysis", "evidence/analysis"),
        ("financials", "financials"), ("assumptions", "financial-assumptions"))}
    for name, body in reads.items():
        assert [(p["from"], p["to"]) for p in body["analysed_periods"]] == [(body["shown_period"]["from"],
                                                                             body["shown_period"]["to"])], name
        assert body["window"]["from"] == body["shown_period"]["from"], name
    period = reads["overview"]["analysed_periods"][0]
    assert period["href"].startswith(f"/api/sites/{CODE}/ev/overview?from=")
    exact = c.get(period["href"]).json()
    assert exact["status"] == reads["overview"]["status"] and exact["status"]["state"] != "UNKNOWN"
    assert exact["analysed_periods"] == [] and exact["shown_period"] is None
    empty = get(c, f"overview?from={z(day[0] + timedelta(days=10))}&to={z(day[0] + timedelta(days=17))}")
    assert empty["analysed_periods"] == [] and empty["shown_period"] is None
    assert empty["status"]["state"] == "UNKNOWN"
