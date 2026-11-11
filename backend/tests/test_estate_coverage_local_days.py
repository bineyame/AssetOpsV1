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


def cov(day_grades=None, days=None, heads=(), tz=None) -> dict:
    # A UTC+3 Site: both UTC dispatch windows touching local day D (index 2) hold a selection, so the UTC rule
    # sees no gap at all.
    days = [day(i) for i in range(N)] if days is None else days
    kw = {} if day_grades is None else {"day_grades": day_grades}
    if tz is not None:
        kw["day_tz"] = tz
    return coverage.site_coverage(Snap(days, heads=list(heads)), T, S, coverage.MINI_GRID, D0, D0 + timedelta(days=N), K,
                                  **kw)


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
    assert claims.day_grades(T, "KB", lo, hi, K) == (
        {days[0]: "COMPLETE", days[1]: "NO_DATA", days[2]: "PENDING"}, "Africa/Addis_Ababa")
    assert seen == [("sid", "MINIGRID", days)]
    assert EstateClaims(lambda: None, lambda: None, lambda code: site).day_grades(T, "KB", lo, hi, K) is None


def test_estate_claims_day_grades_not_expected_day_is_not_expected() -> None:
    from types import SimpleNamespace
    from assetops_backend.chain.claims import EstateClaims, _measures

    ms = _measures("mini_grid")
    d = date(2026, 11, 3)
    facts = SimpleNamespace(days=(d,), none_declared={}, grades={d: {m: {"s": "NOT_EXPECTED"} for m in ms}})
    site = SimpleNamespace(site_id="sid", site_code="KB", domain="mini_grid", timezone=None)
    claims = EstateClaims(lambda: SimpleNamespace(request=lambda t, k: SimpleNamespace(day=lambda *a: facts)),
                          lambda: None, lambda code: site)
    lo, hi = datetime(2026, 11, 3, tzinfo=timezone.utc), datetime(2026, 11, 4, tzinfo=timezone.utc)
    assert claims.day_grades(T, "KB", lo, hi, K)[0] == {d: "NOT_EXPECTED"}


SITE = {"site_code": "KB", "site_type": "MINIGRID"}


def test_local_day_grades_kw_reads_the_injected_provider_at_the_claims_known_at() -> None:
    from types import SimpleNamespace
    seen = []
    coverage.day_grades_provider = lambda *a: seen.append(a) or ({LOCAL[0]: "COMPLETE"}, "Africa/Addis_Ababa")
    lo, hi = D0, D0 + timedelta(days=1)
    try:
        page_one = SimpleNamespace(from_=lo, to=hi, known_at=None)
        assert coverage.local_day_grades_kw(SITE, page_one, {"k": K, "cursor": None}, T) == {
            "day_grades": {LOCAL[0]: "COMPLETE"}, "day_tz": "Africa/Addis_Ababa"}
        assert seen[-1] == (T, "KB", lo, hi, None)  # L1: page one reads at req.known_at (the claims' key)
        explicit = SimpleNamespace(from_=lo, to=hi, known_at=K - timedelta(hours=1))
        coverage.local_day_grades_kw(SITE, explicit, {"k": K, "cursor": None}, T)
        assert seen[-1][4] == K - timedelta(hours=1)
        coverage.local_day_grades_kw(SITE, page_one, {"k": K, "cursor": {"page_one_mode": "live"}}, T)
        assert seen[-1][4] == K  # a cursor page reads at k
        cold = {"site_code": "CC", "site_type": "COLDCHAIN"}
        assert coverage.local_day_grades_kw(cold, page_one, {"k": K, "cursor": None}, T) == {}
        coverage.day_grades_provider = lambda *a: None  # an unreadable chain: today's rule
        assert coverage.local_day_grades_kw(SITE, page_one, {"k": K, "cursor": None}, T) == {}
    finally:
        coverage.day_grades_provider = None
    assert coverage.local_day_grades_kw(SITE, page_one, {"k": K, "cursor": None}, T) == {}


def test_live_request_makes_one_chain_day_read_per_mini_grid_site() -> None:
    """The claims' `claim_days` and the coverage grades share one memoised `chain.day` read (same known_at key)."""
    from types import SimpleNamespace
    from assetops_backend import read_scope
    from assetops_backend.chain.claims import EstateClaims, claim_days

    calls = []
    site = SimpleNamespace(site_id="sid", site_code="KB", domain="mini_grid", timezone="Africa/Addis_Ababa")

    class Req:
        def __init__(self, k=None):
            self.k = k

        def day(self, site_id, site_type, window):
            def read(*args):
                calls.append(args)
                return {}
            read_scope.memo("chain.day", read, T, site_id, window[0], window[-1], self.k)  # k is in the key
            return SimpleNamespace(days=window, grades={}, none_declared={}, rows=(), readiness="NONE", gaps=(),
                                   settled=True, values={})

    claims = EstateClaims(lambda: SimpleNamespace(request=lambda t, k: Req(k)), lambda: None, lambda code: site)
    lo, hi = datetime(2026, 11, 3, tzinfo=timezone.utc), datetime(2026, 11, 6, tzinfo=timezone.utc)
    coverage.day_grades_provider = claims.day_grades
    page_one = SimpleNamespace(from_=lo, to=hi, known_at=None)
    try:
        with read_scope.scope("test"):
            try:
                claim_days(Req(), site, lo, hi)
            except Exception:  # the grade-count of the fake facts is not under test, only the read count
                pass
            coverage.local_day_grades_kw(SITE, page_one, {"k": K, "cursor": None}, T)
    finally:
        coverage.day_grades_provider = None
    assert len(calls) == 1, calls


def test_m1_data_day_without_a_dispatch_selection_is_a_not_analysed_gap() -> None:
    days = [day(i, selected=i != 2) for i in range(N)]
    body = cov(grades(), days=days)  # every local day has readings; the UTC day of D has no selection
    assert body["state"] == "PARTIAL" and body["days"]["requested"] == 7 and body["days"]["checked"] == 6
    assert body["days"]["gaps"] == [{"day": LOCAL[2].isoformat(), "state": "UNASSESSED", "reason": "NOT_ANALYSED"}]
    unavailable = [day(i, available=i != 2) for i in range(N)]
    assert cov(grades(), days=unavailable)["days"]["gaps"][0]["reason"] == "NOT_ANALYSED"
    no_data = cov(grades(d2="NO_DATA"), days=days)  # the grade decides first
    assert no_data["days"]["gaps"][0]["reason"] == "NO_READINGS"


def test_l4_not_expected_day_is_neither_requested_nor_checked() -> None:
    body = cov(grades(d3="NOT_EXPECTED"), days=[day(i) for i in range(N) if i != 3])
    assert body["state"] == "CURRENT"
    assert body["days"]["requested"] == 6 and body["days"]["checked"] == 6 and body["days"]["gaps"] == []
    partial = cov(grades(d3="NOT_EXPECTED", d1="NO_DATA"))
    assert partial["days"]["requested"] == 6 and partial["days"]["checked"] == 5
    assert partial["state"] == "PARTIAL"


def test_l3_finding_starting_after_local_midnight_is_not_withheld_by_a_gap_on_the_day_before() -> None:
    # UTC+3: local D+1 01:00 is D 22:00Z. The UTC day bounds of D reach it; the Site-local bounds (D ends 21:00Z, plus the
    # 20 minute tolerance) do not.
    d = LOCAL[2]
    start = datetime(d.year, d.month, d.day, 22, 0, tzinfo=timezone.utc)
    h = head(start, start + timedelta(hours=1))
    body = cov(grades(d2="NO_DATA"), heads=[h], tz="Africa/Addis_Ababa")
    assert body["state"] == "PARTIAL" and [r["finding_id"] for r in body["rows"]] == [h["finding_id"]]
    assert body["days"]["withheld"] is False
    inside = datetime(d.year, d.month, d.day, 12, 0, tzinfo=timezone.utc)  # local D 15:00: touches D, withheld
    body = cov(grades(d2="NO_DATA"), heads=[head(inside, inside + timedelta(hours=1))], tz="Africa/Addis_Ababa")
    assert body["rows"] == [] and body["days"]["withheld"] is True
