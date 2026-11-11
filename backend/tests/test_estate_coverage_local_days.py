"""DATA-12 (D-E5.38): mini-grid coverage counts the Site's local graded days (the chain's `window_days` and stored day
grades), not UTC dispatch days. Fake one-transaction snapshots; no database."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from assetops_backend.estate import coverage
from test_cov_partial import D0, K, S, T, Snap, day, head

N = 7
LOCAL = [(D0 + timedelta(days=i)).date() for i in range(N)]


def grades(**by_index: str) -> dict[date, str]:
    out = {d: "COMPLETE" for d in LOCAL}
    for i, g in by_index.items():
        out[LOCAL[int(i[1:])]] = g
    return out


def cov(day_grades=None, days=None, heads=()) -> dict:
    # A UTC+3 Site: both UTC dispatch windows touching local day D (index 2) hold a selection, so the UTC rule
    # sees no gap at all.
    days = [day(i) for i in range(N)] if days is None else days
    return coverage.site_coverage(Snap(days, heads=list(heads)), T, S, coverage.MINI_GRID, D0, D0 + timedelta(days=N), K,
                                  **({} if day_grades is None else {"day_grades": day_grades}))


def test_local_no_data_day_is_partial_with_gap() -> None:
    body = cov(grades(d2="NO_DATA"))
    assert body["state"] == "PARTIAL"
    assert body["days"]["requested"] == 7 and body["days"]["checked"] == 6
    assert body["days"]["gaps"] == [{"day": LOCAL[2].isoformat(), "state": "UNASSESSED", "reason": "NO_READINGS"}]
    assert body["days"]["text"] == "6 of 7 days assessed · 1 day not available yet"


def test_none_keeps_utc_rule() -> None:
    body = cov(None)
    assert body["state"] == "CURRENT" and body["days"]["checked"] == 7 and body["days"]["gaps"] == []


def test_all_graded_days_with_data_stay_current() -> None:
    body = cov(grades(d1="PARTIAL", d3="LOW"))
    assert body["state"] == "CURRENT" and body["days"]["checked"] == 7 and body["days"]["gaps"] == []


def test_pending_grade_is_pending_recompute() -> None:
    assert cov(grades(d4="PENDING"))["state"] == "PENDING_RECOMPUTE"


def test_requested_is_the_local_frame_not_the_utc_dispatch_count() -> None:
    body = cov(grades(d2="NO_DATA"), days=[day(i) for i in range(N + 1)])
    assert body["state"] == "PARTIAL" and body["days"]["requested"] == 7


def test_estate_claims_day_grades_is_the_weakest_stored_row_per_window_day() -> None:
    from types import SimpleNamespace
    from assetops_backend.chain.claims import EstateClaims, _measures

    ms = _measures("mini_grid")
    days = (date(2026, 11, 3), date(2026, 11, 4), date(2026, 11, 5))
    full = {m: {"s": "COMPLETE"} for m in ms}
    facts = SimpleNamespace(days=days, none_declared={}, grades={
        days[0]: full, days[1]: {}, days[2]: {**full, ms[0]: {"s": "PENDING"}}})
    seen = []

    class Req:
        def day(self, site_id, site_type, window):
            seen.append((site_id, site_type, window))
            return facts

    site = SimpleNamespace(site_id="sid", site_code="KB", domain="mini_grid", timezone="Africa/Addis_Ababa")
    claims = EstateClaims(lambda: SimpleNamespace(request=lambda t, k: Req()), lambda: None, lambda code: site)
    lo, hi = datetime(2026, 11, 3, tzinfo=timezone.utc), datetime(2026, 11, 6, tzinfo=timezone.utc)
    assert claims.day_grades(T, "KB", lo, hi, K) == {days[0]: "COMPLETE", days[1]: "NO_DATA", days[2]: "PENDING"}
    assert seen == [("sid", "MINIGRID", days)]
    assert EstateClaims(lambda: None, lambda: None, lambda code: site).day_grades(T, "KB", lo, hi, K) is None


def test_local_day_grades_kw_reads_the_injected_provider() -> None:
    seen = []
    coverage.day_grades_provider = lambda *a: seen.append(a) or {LOCAL[0]: "COMPLETE"}
    try:
        site = {"site_code": "KB", "site_type": "MINIGRID"}
        assert coverage.local_day_grades_kw(site, D0, D0 + timedelta(days=1), K, T) == {
            "day_grades": {LOCAL[0]: "COMPLETE"}}
        assert seen == [(T, "KB", D0, D0 + timedelta(days=1), K)]
        assert coverage.local_day_grades_kw({"site_code": "CC", "site_type": "COLDCHAIN"}, D0, D0, K, T) == {}
        coverage.day_grades_provider = lambda *a: None  # an unreadable chain: today's rule
        assert coverage.local_day_grades_kw(site, D0, D0, K, T) == {}
    finally:
        coverage.day_grades_provider = None
    assert coverage.local_day_grades_kw({"site_code": "KB", "site_type": "MINIGRID"}, D0, D0, K, T) == {}
