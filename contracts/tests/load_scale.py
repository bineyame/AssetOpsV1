"""One rule for wall-time bounds in tests: the bound is scaled by machine load, so a busy host does not fail a test
that passes alone (owner approval 2026-11-21). factor = clamp(load1 / cpu_count, 1, 4); a bound never shrinks, and
never grows past 4x, so a real slowdown of more than 4x (or of more than the scaled bound) still fails."""
from __future__ import annotations

import os

LOAD_SCALE_CAP = 4.0


def load_factor(load1: float | None = None, cpus: int | None = None) -> float:
    if load1 is None:
        try:
            load1 = os.getloadavg()[0]
        except (OSError, AttributeError):
            return 1.0
    cpus = cpus or os.cpu_count() or 1
    return min(LOAD_SCALE_CAP, max(1.0, load1 / cpus))


def scale_wall(seconds: float, load1: float | None = None, cpus: int | None = None) -> float:
    return seconds * load_factor(load1, cpus)
