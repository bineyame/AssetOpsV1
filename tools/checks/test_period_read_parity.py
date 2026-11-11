"""ANY-1 AR-0: the parity harness self-test (no database). One deliberate mismatch must fail."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import period_read_parity as parity  # noqa: E402


def test_self_test_passes() -> None:
    assert parity.self_test() == []
    assert parity.main(["--self-test"]) == 0


def test_unaligned_portfolio_cases_randomise_both_ends() -> None:
    from datetime import date

    cases = [c for seed in range(6) for c in parity.seeded_cases(seed, 24, date(2026, 10, 1), date(2026, 10, 31))
             if c.family == "portfolio_any_range"]
    ends = {parity._end_unaligned(c.path) for c in cases}
    assert ends == {True, False}  # both kinds drawn, and every span stays in (0, 31] days
    assert all(0 < parity.portfolio_days(c.path) <= parity.MAX_PORTFOLIO_DAYS for c in cases)


def test_no_row_with_two_revisions_is_a_failure_not_a_skip(monkeypatch, tmp_path) -> None:
    import types

    probe = types.ModuleType("chain_perf_probe")
    probe.client = lambda url, work: types.SimpleNamespace(
        get=lambda path: types.SimpleNamespace(status_code=200, content=b"{}"))
    monkeypatch.setitem(sys.modules, "chain_perf_probe", probe)
    monkeypatch.setattr(parity, "story_cases", lambda: [])
    monkeypatch.setattr(parity, "between_revisions_case", lambda url: None)
    report = parity.run("x", tmp_path, None, 1, 6, "")
    assert [(o.case.id, o.verdict) for o in report.failed] == [("any.between_revisions", "MISSING")]
    found = parity.Case("any.between_revisions.site_day_snapshot", "/api/sites/X/outcome-board?date=2026-10-20",
                        "historical_between_revisions")
    monkeypatch.setattr(parity, "between_revisions_case", lambda url: found)
    report = parity.run("x", tmp_path, None, 1, 6, "")
    assert not report.failed and report.outcomes[-1].case == found


def test_self_test_is_not_vacuous(monkeypatch) -> None:
    """Break the comparison (a compare that never reports): the self-test must then fail."""
    monkeypatch.setattr(parity, "compare", lambda cases, oracle, candidate, *clock: parity.Report(
        [parity.Outcome(c, "PASS") for c in cases]))
    problems = parity.self_test()
    assert any("deliberate byte mismatch" in p for p in problems), problems
    assert any("unstable oracle" in p for p in problems), problems
    assert any("real body difference" in p for p in problems), problems
    assert parity.main(["--self-test"]) == 1


def test_live_now_normaliser_is_not_vacuous(monkeypatch) -> None:
    """No normalising: the live echo is caught. Normalising every known_at: historical and stored values are caught."""
    monkeypatch.setattr(parity, "normalise_live_now", lambda body, before, after: body)
    assert any("echoed now was not normalised" in p for p in parity.self_test())
    monkeypatch.setattr(parity, "normalise_live_now", lambda body, before, after: parity._SELECTION_TOKEN.sub(
        parity.LIVE_TOKEN, parity._KNOWN_AT.sub(parity.LIVE_NOW, body)))
    assert any("stored (not now)" in p for p in parity.self_test())
    monkeypatch.setattr(parity, "is_live", lambda path: True)
    problems = parity.self_test()
    assert any("historical read's known_at was normalised" in p for p in problems)
    assert any("historical read's selection_token difference was normalised" in p for p in problems)


def test_live_selection_token_normaliser_is_not_vacuous(monkeypatch) -> None:
    """The now echo normalised but not the live `selection_token` (which hashes now): the live case is caught."""
    monkeypatch.setattr(parity, "normalise_live_now",
                        lambda body, before, after: parity._KNOWN_AT.sub(parity.LIVE_NOW, body))
    assert any("echoed now was not normalised" in p for p in parity.self_test())


def test_live_now_normaliser_touches_only_the_now_echo() -> None:
    body = b'{"known_at":"2026-11-11T13:52:51Z","w":{"known_at":"2026-11-07T21:00:00Z"},"day":"2026-11-11T13:52:51Z"}'
    at = parity.datetime(2026, 11, 11, 13, 52, 51, tzinfo=parity.UTC).timestamp()
    assert parity.normalise_live_now(body, at - 0.4, at + 0.2) == (
        b'{"known_at":"<live-now>","w":{"known_at":"2026-11-07T21:00:00Z"},"day":"2026-11-11T13:52:51Z"}')
