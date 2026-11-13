"""DISP-1 (D-ANY.11) no-DB: `MoneyEligibility.for_finding_on(select_days=...)` reads the bracket's days from the
caller's stored-day source, never from `select_dispatch_days_on`; a short list fails closed."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from assetops_backend.analytics.dispatch_v3 import MODEL_VERSION
from assetops_backend.analytics.finding_episode import MATCHER_VERSION
from assetops_backend.financials.money_eligibility import ELIGIBLE, PENDING_REASSESSMENT, MoneyEligibility

D = date(2026, 10, 24)
K = datetime(2026, 10, 25, tzinfo=timezone.utc)
HEAD = {"finding_id": "f-1", "finding_revision_id": "rev-3", "revision_no": 3, "matcher_version": MATCHER_VERSION,
        "episode_start": datetime(2026, 10, 24, 6, 5, tzinfo=timezone.utc),
        "episode_end": datetime(2026, 10, 24, 8, tzinfo=timezone.utc)}


class Findings:
    def index_snapshot_on(self, c, t, s, domain, analytic, known_at):
        return {"heads": [HEAD], "match_pass": {"match_pass_id": "mp", "matched_through_selection_seq": 5},
                "deferred_windows": []}

    def money_revision_on(self, c, t, s, rev):
        return {"claim": {"end_reason": "OPEN_BOUND", "series_limits": []}, "generator_asset_id": "G1"}

    def index_lineage_on(self, c, t, s, revs, known_at):
        return {"assessments": [{"assessment_revision_id": "win-24", "scope": "WINDOW"}]}


def stored_day(available=True):
    return {"day": D, "available": available, "unavailable_reasons": [] if available else ["NOT_BUILT"],
            "window_start": datetime(2026, 10, 24, tzinfo=timezone.utc), "status": "CURRENT", "jobs": [],
            "window_assessment_revision_id": "win-24",
            "selection": {"seq": 4, "run_id": "run-1", "model_version": MODEL_VERSION, "cohort": {"limits": []}}}


class Days:
    def __init__(self, rows):
        self.rows, self.calls = rows, 0

    def select_dispatch_days_on(self, c, t, s, lo, hi, known_at):
        self.calls += 1
        return self.rows


def gate(rows, supplied=None):
    days = Days(rows)
    me = MoneyEligibility(None, Findings(), days=days)
    seen = []
    kw = {} if supplied is None else {"select_days": lambda f, to: seen.append((f, to)) or supplied}
    return me.for_finding_on(None, uuid4(), uuid4(), "f-1", K, **kw), days, seen


def test_select_days_given_never_calls_select_dispatch_days_on() -> None:
    out, days, seen = gate([stored_day()], [stored_day()])
    assert days.calls == 0 and len(seen) == 1 and out["state"] == ELIGIBLE


def test_stored_days_give_the_same_result_as_compose() -> None:
    for ok in (True, False):
        stored, _, _ = gate([stored_day(ok)], [stored_day(ok)])
        composed, days, _ = gate([stored_day(ok)])
        assert days.calls == 1 and stored == composed
        assert stored["state"] == (ELIGIBLE if ok else PENDING_REASSESSMENT)


def test_select_days_works_without_a_days_store() -> None:
    me = MoneyEligibility(None, Findings(), days=None)
    me.days = None
    out = me.for_finding_on(None, uuid4(), uuid4(), "f-1", K, select_days=lambda f, to: [stored_day()])
    assert out["state"] == ELIGIBLE
    assert me.for_finding_on(None, uuid4(), uuid4(), "f-1", K)["pending_reasons"] == ["AS_OF_GATE_NOT_WIRED"]


D2 = date(2026, 10, 25)
HEAD2 = {**HEAD, "episode_start": datetime(2026, 10, 24, 22, tzinfo=timezone.utc),
         "episode_end": datetime(2026, 10, 25, 2, tzinfo=timezone.utc)}  # the 6 h bracket spans D and D2


class Findings2(Findings):
    def index_snapshot_on(self, c, t, s, domain, analytic, known_at):
        return {**super().index_snapshot_on(c, t, s, domain, analytic, known_at), "heads": [HEAD2]}

    def index_lineage_on(self, c, t, s, revs, known_at):
        return {"assessments": [{"assessment_revision_id": "win-24", "scope": "WINDOW"},
                                {"assessment_revision_id": "win-25", "scope": "WINDOW"}]}


def compose_day(d):
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return {**stored_day(), "day": d, "window_start": start, "window_end": start.replace(day=d.day + 1)}


class HistoricalSnap:
    """An `EstateSnapshot`-like stub: a historical basis whose compose gives both days."""
    basis_historical = True
    continuation = False

    def dispatch_days(self, t, s, from_, to, k):
        return [compose_day(D), compose_day(D2)]


def test_absent_run_in_the_bracket_equals_compose_and_kill_switch_equals_compose(monkeypatch) -> None:
    """DISP-1 review Low: the adapter's `select_days` (coverage.dispatch_days) over one stored day plus one absent run
    (D-ANY.10) gives the `select_days=None` compose result; so does a provider that serves no kind (None)."""
    from assetops_backend.chain.dispatch_day_rows import ABSENT_MARK
    from assetops_backend.estate import coverage
    snap, t, s = HistoricalSnap(), uuid4(), uuid4()
    absent = {**compose_day(D2), ABSENT_MARK: True, "selection": None, "status": "UNASSESSED", "jobs": []}
    served = [compose_day(D), absent]
    me = MoneyEligibility(None, Findings2(), days=Days([compose_day(D), compose_day(D2)]))
    oracle = me.for_finding_on(None, t, s, "f-1", K)
    assert oracle["state"] == ELIGIBLE
    for provided in (served, None):
        monkeypatch.setattr(coverage, "dispatch_rows_provider", lambda *a, _p=provided: _p)
        got = me.for_finding_on(None, t, s, "f-1", K, select_days=lambda f, to: coverage.dispatch_days(snap, t, s, f, to, K))
        assert got == oracle


def test_short_day_list_fails_closed() -> None:
    out, _, _ = gate([stored_day()], [])
    assert out["state"] == PENDING_REASSESSMENT
    assert out["pending_reasons"][0].startswith("HISTORICAL_DAY_UNAVAILABLE: DAY 2026-10-24")
