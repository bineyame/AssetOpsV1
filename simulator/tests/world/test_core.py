"""DS1a T5, T6, T7: allocation, no floats, months (spec §10)."""

from __future__ import annotations

import itertools
import re
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

import pytest

from assetops_simulator.world.allocate import allocate, split_to_days
from assetops_simulator.world.canonical import canonical_bytes
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.months import MONTH_ABBR, day_class, days_in, period_end
from assetops_simulator.world.view import ManifestView

from .conftest import REPOSITORY_ROOT

WORLD = REPOSITORY_ROOT / "simulator" / "assetops_simulator" / "world"


# ---- T5 allocation --------------------------------------------------------------


def _reference(total: int, weights: list[int]) -> list[int]:
    """Largest remainder written out independently: exact shares, floors, leftover by
    descending remainder, ties to the lower index."""
    whole = sum(weights)
    shares = [Fraction(total * w, whole) for w in weights]
    floors = [s.numerator // s.denominator for s in shares]
    left = total - sum(floors)
    ranked = sorted(range(len(weights)), key=lambda i: (floors[i] - shares[i], i))
    for i in ranked[:left]:
        floors[i] += 1
    return floors


def test_t5_hand_cases() -> None:
    assert allocate(10, [Fraction(1)] * 3) == [4, 3, 3]
    assert allocate(7, [Fraction(0), Fraction(1)]) == [0, 7]
    assert allocate(5, [Fraction(1), Fraction(1)]) == [3, 2]
    assert allocate(1, [Fraction(1), Fraction(1)]) == [1, 0]  # tie to the lower index
    assert allocate(2, [Fraction(1)] * 4) == [1, 1, 0, 0]


@pytest.mark.parametrize(
    "total, weights",
    [(-1, [Fraction(1)]), (5, [Fraction(-1), Fraction(2)]), (5, [Fraction(0), Fraction(0)]), (5, [])],
)
def test_t5_refusals(total: int, weights: list) -> None:
    with pytest.raises(ValueError, match=r"^ALLOCATE_BAD_INPUT$"):
        allocate(total, weights)


def test_t5_exhaustive() -> None:
    checked = 0
    for n in range(1, 5):
        for weights in itertools.product((0, 1, 2, 3), repeat=n):
            if sum(weights) == 0:
                continue
            for total in range(0, 51):
                got = allocate(total, [Fraction(w) for w in weights])
                assert sum(got) == total
                assert got == _reference(total, list(weights)), (total, weights)
                checked += 1
    assert checked > 10_000


def test_t5_split_to_days() -> None:
    days = [date(2026, 7, 1) + timedelta(days=i) for i in range(31)]
    weekday = lambda d: Fraction(1) if d.isoweekday() <= 5 else Fraction(1, 2)  # noqa: E731
    parts = split_to_days(1000, days, weekday)
    assert len(parts) == 31 and sum(parts) == 1000
    assert parts == allocate(1000, [weekday(d) for d in days])
    assert split_to_days(0, days, weekday) == [0] * 31


# ---- T6 no floats ----------------------------------------------------------------


def _walk_types(obj, path="$"):
    if isinstance(obj, bool):
        raise AssertionError(f"bool at {path}")
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert isinstance(k, str), path
            yield from _walk_types(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_types(v, f"{path}[{i}]")
    else:
        yield path, type(obj)


def test_t6_output_types(view: dict) -> None:
    kinds = {t for _, t in _walk_types(generate_history(view))}
    assert kinds <= {int, str}, kinds
    assert int in kinds and str in kinds


def test_t6_canonical_refuses_float() -> None:
    with pytest.raises(TypeError, match=r"^CANONICAL_FLOAT$"):
        canonical_bytes({"a": [1, {"b": 0.5}]})


@pytest.mark.parametrize("bad", [True, date(2026, 10, 1), None])
def test_t6_view_refuses_other_types(bad) -> None:
    with pytest.raises(ValueError, match=r"^VIEW_TYPE "):
        ManifestView.from_document({"manifest_version": 1, "as_of": bad})


def test_t6_view_float_becomes_repr() -> None:
    v = ManifestView.from_document({"currency": "USD", "manifest_version": 1, "as_of": "x",
                                    "tenants": [{"tenant": "t", "prices": {"a": 3420.0, "b": 0.25}}]})
    assert v["tenants"][0]["prices"] == {"a": "3420.0", "b": "0.25"}


GREPS = [
    r"\bfloat\(",
    r"^\s*(import|from)\s+(random|time|secrets)\b",
    r"\.(now|today|utcnow)\(",
    r"os\.environ|getenv",
]


@pytest.mark.parametrize("pattern", GREPS)
def test_t6_greps(pattern: str) -> None:
    files = sorted(WORLD.rglob("*.py"))
    assert files, "world package not found"
    hits = [f"{p.name}:{i}" for p in files
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if re.search(pattern, line)]
    assert hits == []


# ---- T7 months -------------------------------------------------------------------

DAY_CLASSES = {"WD": [1, 2, 3, 4, 5], "SA": [6], "SU": [7]}


@pytest.mark.parametrize(
    "month, days, end, counts",
    [("2026-07", 31, "2026-07-31", (23, 4, 4)), ("2026-08", 31, "2026-08-31", (21, 5, 5)),
     ("2026-09", 30, "2026-09-30", (22, 4, 4)), ("2026-10", 31, "2026-10-31", (22, 5, 4))],
)
def test_t7_months(month: str, days: int, end: str, counts: tuple) -> None:
    assert days_in(month) == days
    assert period_end(month).isoformat() == end
    y, m = (int(x) for x in month.split("-"))
    classes = [day_class(date(y, m, i), DAY_CLASSES) for i in range(1, days + 1)]
    assert (classes.count("WD"), classes.count("SA"), classes.count("SU")) == counts
    assert MONTH_ABBR[month[5:]] == {"07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct"}[month[5:]]


def test_t7_generated_blocks_carry_calendar(view: dict) -> None:
    hist = generate_history(view)
    for sites in hist["tenants"].values():
        for months in sites.values():
            assert {m: (b["period_days"], b["period_end"]) for m, b in months.items()} == {
                "2026-07": (31, "2026-07-31"), "2026-08": (31, "2026-08-31"), "2026-09": (30, "2026-09-30")}
