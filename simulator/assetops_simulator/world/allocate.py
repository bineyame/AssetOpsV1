"""Exact largest-remainder allocation (spec §4.4)."""

from __future__ import annotations

from datetime import date
from fractions import Fraction
from typing import Callable


def allocate(total: int, weights: list[Fraction]) -> list[int]:
    """Split a non-negative integer by weight. Parts are floored, then the leftover
    units go one each by largest remainder; ties go to the lower index."""
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("ALLOCATE_BAD_INPUT")
    exact_weights = []
    for weight in weights:
        if isinstance(weight, bool) or not isinstance(weight, (int, Fraction)) or weight < 0:
            raise ValueError("ALLOCATE_BAD_INPUT")
        exact_weights.append(Fraction(weight))
    whole = sum(exact_weights, Fraction(0))
    if whole == 0:
        raise ValueError("ALLOCATE_BAD_INPUT")
    shares = [total * w / whole for w in exact_weights]
    parts = [s.numerator // s.denominator for s in shares]
    leftover = total - sum(parts)
    by_remainder = sorted(range(len(parts)), key=lambda i: (-(shares[i] - parts[i]), i))
    for i in by_remainder[:leftover]:
        parts[i] += 1
    return parts


def split_to_days(total: int, days: list[date], weight: Callable[[date], Fraction]) -> list[int]:
    """`allocate` over the given days, in the order given (for DS2 and DS3)."""
    return allocate(total, [weight(day) for day in days])
