"""DD4.6 (D-DD.144, owner-approved 22 Nov; D-DD.143): the cold energy model restated from the meter, and Kirinyaga's
efficiency condition frozen as a declared constant.

- The writer's `f_m` is `telemetry_cold.EFFICIENCY_CONDITION`, no longer read from `M`'s period kwh / kwh_model (which
  now follow the meter); parity golden `golden/efficiency_condition_main.json`, captured from main 6e3c02ab5's view.
- `M`'s `energy_model` is the ruling's own fit: the ordinary least-squares line of the metered room-month kWh,
  normalised to 24 C by `M`'s form, on `crate_days`, over Mwea and Thika July-September (Kirinyaga excluded);
  `base_kwh` to whole kWh, `k` to 4 decimals, half-even. The metered kWh are the committed DD4.4 plant
  (`fixtures/measured/harvest-cold.measured.json`).
- `M`'s October cold `kwh` leaves are the meter's (D-DD.20) and `kwh_model` the restated model's.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from pathlib import Path

from assetops_simulator.world import telemetry_cold
from assetops_simulator.world.telemetry_cold import cold_books_for, day_ambient

from .books_support import COLD, build, m_tenant, manifest, measured_fixture
from .conftest import REPOSITORY_ROOT, load_fixture

HERE = Path(__file__).resolve().parent
GOLDEN = json.loads((HERE / "golden" / "efficiency_condition_main.json").read_text(encoding="utf-8"))["efficiency"]
HISTORY = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4" / "history.json"
FIT_ROOMS = {"COLD-MWEA": "Room A · Mwea", "COLD-THIKA": "Room B · Thika"}
FIT_MONTHS = ("2026-07", "2026-08", "2026-09")
REFERENCE_C = Fraction(24)


def _decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def test_efficiency_condition_is_the_main_view() -> None:
    """D-DD.144: Kirinyaga's table is a declared constant with D-DD.143's values; Mwea and Thika have none."""
    table = telemetry_cold.EFFICIENCY_CONDITION
    assert {code: dict(months) for code, months in table.items()} == {k: v for k, v in GOLDEN.items() if v}
    assert all(Fraction(f) > 1 for months in table.values() for f in months.values())


def test_books_take_the_constant_not_the_period_kwh() -> None:
    """A changed period kwh (as the meter now states it) does not move the writer's `f_m`."""
    view = load_fixture()
    cold = next(t for t in view["tenants"] if t["tenant"] == COLD)
    for site in cold["sites"]:
        site["period"]["actual"]["kwh"] = "2113.603" if site["code"] == "COLD-KIRI" else "1576.3"
    built_view, history, records, _books = build(view)
    out = cold_books_for(built_view, history, records)
    assert out["COLD-KIRI"]["efficiency"] == GOLDEN["COLD-KIRI"]
    assert out["COLD-MWEA"]["efficiency"] == {} and out["COLD-THIKA"]["efficiency"] == {}


def _month_factor(month: str, cooling: dict) -> Fraction:
    """`M`'s form at the month's mean ambient: 1 + 0.025 x (ambient - 24)."""
    first = date.fromisoformat(f"{month}-01")
    days = [first + timedelta(days=i) for i in range(40) if (first + timedelta(days=i)).month == first.month]
    mean = sum((day_ambient(d, cooling, "COLD") for d in days), Fraction(0)) / len(days)
    return 1 + Fraction(1, 40) * (mean - REFERENCE_C)


def test_energy_model_is_the_rulings_fit() -> None:
    m = manifest()
    hist = m["history"]
    cooling = {"cooling": hist["families"]["cooling"], "seasons": hist["seasons"], "day_classes": hist["day_classes"]}
    history = json.loads(HISTORY.read_text(encoding="utf-8"))["tenants"][COLD]
    metered = measured_fixture(COLD)["sites"]
    points = [(Fraction(history[room][month]["actual"]["crate_days"]),
               Fraction(metered[code][month]["room_kwh"]) / _month_factor(month, cooling))
              for code, room in FIT_ROOMS.items() for month in FIT_MONTHS]
    n = len(points)
    sx, sy = sum(x for x, _ in points), sum(y for _, y in points)
    sxx, sxy = sum(x * x for x, _ in points), sum(x * y for x, y in points)
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    base = (sy - slope * sx) / n
    model = m_tenant(COLD)["energy_model"]
    assert Decimal(str(model["base_kwh"])) == _decimal(base).quantize(Decimal(1), ROUND_HALF_EVEN) == Decimal(1304)
    assert Decimal(str(model["k_kwh_per_crate_day"])) == _decimal(slope).quantize(Decimal("0.0001"), ROUND_HALF_EVEN) \
        == Decimal("0.0554")
    assert "D-DD.144" in model["status"]


def test_october_kwh_is_the_meter_and_kwh_model_the_restated_model() -> None:
    cold = m_tenant(COLD)
    base = Decimal(str(cold["energy_model"]["base_kwh"]))
    k = Decimal(str(cold["energy_model"]["k_kwh_per_crate_day"]))
    metered = measured_fixture(COLD)["sites"]
    for site in cold["sites"]:
        actual, plan = site["period"]["actual"], site["period"]["plan"]
        assert Decimal(str(actual["kwh"])) == Decimal(metered[site["code"]]["2026-10"]["room_kwh"]), site["code"]
        assert Decimal(str(actual["kwh_model"])) == base + k * Decimal(actual["crate_days"]), site["code"]
        assert Decimal(str(plan["kwh"])) == base + k * Decimal(plan["crate_days"]), site["code"]
