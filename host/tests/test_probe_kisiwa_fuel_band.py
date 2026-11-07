"""DIESEL-1 F0 (§8.3): `fuel-balance-1` on hand-built terms. L0, no DB, no simulator run."""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from probe_kisiwa_fuel import balance, reporting_gap_minutes  # noqa: E402

NIGHT = Fraction(26057, 600)  # D0's night litres, all loaded


def terms(opening, closing, deliveries=(), loaded=NIGHT, idle_hours=0, gap=0):
    return {"opening": Fraction(opening), "closing": Fraction(closing), "deliveries": list(deliveries),
            "loaded_litres": Fraction(loaded), "idle_hours": Fraction(idle_hours), "gap_minutes": gap}


def test_the_incident_night_is_unexplained_with_the_exact_band() -> None:
    result = balance(terms(600, 600 - NIGHT - 120, gap=105))
    drop = NIGHT + 120
    assert result["residual_low"] == drop - Fraction(11, 10) * NIGHT - 20
    assert result["residual_high"] == drop - Fraction(9, 10) * NIGHT + 20
    # 100 - 43.428/10 = 95.657 and 140 + 43.428/10 = 144.343 (the ruling's "about [95.7, 144.3]").
    assert result["residual_low"] == 100 - NIGHT / 10
    assert result["residual_high"] == 140 + NIGHT / 10
    assert result["state"] == "UNEXPLAINED"


def test_a_clean_night_contains_zero() -> None:
    result = balance(terms(600, 600 - NIGHT))
    assert result["residual_low"] <= 0 <= result["residual_high"]
    assert result["state"] == "WITHIN_MARGIN"


def test_the_delivery_night_is_within_the_margin() -> None:
    result = balance(terms(600, 600 - NIGHT + 300, deliveries=(300,)))
    assert result["residual_low"] == -Fraction(11, 10) * NIGHT + NIGHT - 3 - 20
    assert result["state"] == "WITHIN_MARGIN"


def _with_low(low: Fraction) -> dict:
    # residual_low = (O - C) - use_high - 20 with no deliveries and no use.
    return balance(terms(low + 20, 0, loaded=0))


def test_materiality_edge() -> None:
    assert _with_low(Fraction(40))["state"] == "UNEXPLAINED"
    assert _with_low(Fraction(39999, 1000))["state"] == "BELOW_MATERIALITY"


def test_excess_when_residual_high_is_negative() -> None:
    result = balance(terms(0, 100, loaded=0))
    assert result["residual_high"] == -80
    assert result["state"] == "EXCESS"


def test_missing_edges_are_not_assessed() -> None:
    assert balance({**terms(1, 1), "opening": None})["limitation"] == "MISSING_OPENING"
    assert balance({**terms(1, 1), "closing": None})["limitation"] == "MISSING_CLOSING"


def test_gap_spans_of_60_and_61_minutes() -> None:
    assert reporting_gap_minutes([0, 60, 120], 0, 120) == 0
    assert reporting_gap_minutes([0, 61, 120], 0, 120) == 61
    assert reporting_gap_minutes([15, 30], 0, 120) == 90  # edge to edge
