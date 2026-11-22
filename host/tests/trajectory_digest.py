"""0K4a: one trajectory digest, the pin of a model version's physics (D-0K4.20).

`trajectory_digest(result)` is the sha256 hex of a canonical UTF-8 text with one line per boundary: the offset in
minutes, then sorted `key=value` pairs of the boundary's stocks, interval measurements, discrete states and discrete
states for the step. Exact values are written as `str(Fraction(v))`, states as their code. Two trajectories share a
digest only when every one of those values is equal at every boundary.

N9 (`test_0k4a_dispatch_v8.py`) pins the v7 8-day Kobo season with it, N12 pins v8. A change to either literal is a
new model version, never an edit.
"""

from __future__ import annotations

import hashlib
from fractions import Fraction


def _pairs(tag: str, rows) -> str:
    return tag + ":" + ",".join(f"{key}={value}" for key, value in sorted(rows))


def _exact(rows):
    return ((key, str(Fraction(value))) for key, value in rows)


def canonical_text(result) -> str:
    """The text `trajectory_digest` hashes: one line per boundary."""
    lines = []
    for boundary in result.boundaries:
        lines.append("|".join((
            str(boundary.offset_minutes),
            _pairs("s", _exact(boundary.stocks)),
            _pairs("m", _exact(boundary.interval_measurements)),
            _pairs("d", boundary.discrete),
            _pairs("ds", boundary.discrete_for_step),
        )))
    return "\n".join(lines) + "\n"


def trajectory_digest(result) -> str:
    return hashlib.sha256(canonical_text(result).encode("utf-8")).hexdigest()


__all__ = ["canonical_text", "trajectory_digest"]
