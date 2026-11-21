"""0K4a: `mini-grid` v8, the generator takes the load (spec §3, D-0K4.2 to D-0K4.4, D-0K4.20, D-0K4.22).

The kernel runs here; every expected value comes from this file's own reader of the trajectory (W2), never from the
pack's split or 0K4b's curve. Commit 1 holds N9; v8's tests (N1-N8, N10-N13) arrive with v8 itself (commit 3).
"""

from __future__ import annotations

from functools import cache

from assetops_simulator.kernel.execute import execute

from execution_adapter import model_for
from kobo_season import base_run, season_inputs
from trajectory_digest import trajectory_digest

#: The v7 8-day Kobo season digest, computed on `main` b96d5e978 with only `trajectory_digest.py` added (packet,
#: pre-flight). A change here is a change to v1-v7, which 0K4a must never make.
V7_SEASON_8_DIGEST = "8eb9c44c38f31a77a8faf6e7e9f90fd2c62112dbe0d01c6a3243b7dae783f280"


@cache
def _v7_season(days: int):
    run = base_run(days)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    trajectory = execute(season_inputs(run, days), model_for(run))
    assert trajectory.outcome == "COMPLETED", trajectory.failure
    return trajectory


def test_n9_v7_is_untouched() -> None:
    """v1-v7 untouched (D-0K4.20): the v7 8-day season digest equals the pre-flight literal. A change here is a new
    model version, never an edit."""
    assert trajectory_digest(_v7_season(8)) == V7_SEASON_8_DIGEST
