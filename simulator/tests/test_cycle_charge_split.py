"""0K4a S1-S10: `cycle_charge_split`, D-0K4.3 and D-0K4.4 for one segment of a RUNNING generator (spec §2.2, §3).

Every expected value is a hand literal (W2): no row calls the function to get its own answer. Units are kW.
"""

from __future__ import annotations

from fractions import Fraction as F
from itertools import product

import pytest

from assetops_simulator.packs.mini_grid import CycleSplit, cycle_charge_split

FIELDS = ("pv_to_load", "pv_to_battery", "curtailed_pv", "generator_to_load", "generator_to_battery",
          "battery_to_load", "unserved")

#: (case, (D, A, R, C, M, dis), (pv load, pv bat, curt, gen load, gen bat, bat load, unserved), below minimum)
CASES = (
    ("S1 support", (75, 0, 40, 30, 12, 30), (0, 0, 0, 40, 0, 30, 5), False),
    ("S2 night charge", (13, 0, 40, 30, 12, 0), (0, 0, 0, 13, 27, 0, 0), False),
    ("S3 with PV", (20, 15, 40, 30, 12, 0), (15, 0, 0, 5, 30, 0, 0), False),
    ("S4 minimum load, curtail", (15, 50, 40, 30, 12, 0), (15, 18, 17, 0, 12, 0, 0), False),
    ("S5 nothing to absorb", (5, 50, 40, 2, 12, 0), (0, 0, 50, 5, 2, 0, 0), True),
    ("S6 fuel-capped", (13, 0, 10, 30, 12, 30), (0, 0, 0, 10, 0, 3, 0), False),
    ("S7 at the boundary", (40, 0, 40, 30, 12, 30), (0, 0, 0, 40, 0, 0, 0), False),
    ("S10 no rating, M > R", (5, 15, 0, 2, 12, 0), (5, 2, 8, 0, 0, 0, 0), False),
)


@pytest.mark.parametrize("case, args, expected, below", CASES, ids=[c[0] for c in CASES])
def test_s1_to_s7_and_s10_literal_rows(case, args, expected, below) -> None:
    split = cycle_charge_split(*(F(a) for a in args))
    assert isinstance(split, CycleSplit)
    assert tuple(getattr(split, name) for name in FIELDS) == tuple(F(e) for e in expected), case
    assert split.below_minimum is below, case


def test_s8_invariants_over_the_grid() -> None:
    grid = product((0, 5, 13, 40, 75), (0, 15, 50), (0, 10, 40), (0, 2, 30), (0, 12), (0, 30))
    seen = 0
    for D, A, R, C, M, dis in grid:
        D, A, R, C, M, dis = (F(v) for v in (D, A, R, C, M, dis))
        s = cycle_charge_split(D, A, R, C, M, dis)
        values = [getattr(s, name) for name in FIELDS]
        where = (D, A, R, C, M, dis, values)
        assert all(isinstance(v, F) and v >= 0 for v in values), where
        assert s.pv_to_load + s.pv_to_battery + s.curtailed_pv == A, where
        assert s.pv_to_battery + s.generator_to_battery <= C, where
        assert s.battery_to_load == 0 or D > A + R, where
        assert s.pv_to_load + s.generator_to_load + s.battery_to_load + s.unserved == D, where
        assert not s.below_minimum or (D + C < M and D + C < R), where
        seen += 1
    assert seen == 5 * 3 * 3 * 3 * 2 * 2


@pytest.mark.parametrize("position", range(6))
@pytest.mark.parametrize("bad", [13.0, F(-1)], ids=["float", "negative"])
def test_s9_a_float_or_a_negative_argument_raises(position, bad) -> None:
    args = [F(13), F(0), F(40), F(30), F(12), F(0)]
    args[position] = bad
    with pytest.raises((TypeError, ValueError)):
        cycle_charge_split(*args)
