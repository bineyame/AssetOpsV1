"""ANY-1 AR-0: the parity harness self-test (no database). One deliberate mismatch must fail."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import period_read_parity as parity  # noqa: E402


def test_self_test_passes() -> None:
    assert parity.self_test() == []
    assert parity.main(["--self-test"]) == 0


def test_self_test_is_not_vacuous(monkeypatch) -> None:
    """Break the comparison (a compare that never reports): the self-test must then fail."""
    monkeypatch.setattr(parity, "compare", lambda cases, oracle, candidate: parity.Report(
        [parity.Outcome(c, "PASS") for c in cases]))
    problems = parity.self_test()
    assert any("deliberate byte mismatch" in p for p in problems), problems
    assert any("unstable oracle" in p for p in problems), problems
    assert parity.main(["--self-test"]) == 1
