"""Units of the canonical format v1 and the leaf catalogue (2a spec §4; D-2A.4).

Six dimensions: `KWH`, `L`, `MONEY`, `DAY`, `HOUR`, `MINUTE`. Counts (assets,
buses, chargers, crates, batches, visits) are dimensionless (`ONE`); a night, a
bus-night and a missed departure are `DAY`. No conversion exists between `DAY`,
`HOUR` and `MINUTE`: only a declared factor converts (`hours_per_day`,
`minutes_per_day`).

Canonical text: `"1"` for `ONE`; otherwise the numerator dimensions joined by
`*` (`1` when no exponent is positive), then, if any, `/` and the denominator
dimensions joined by `*`; each dimension is repeated per exponent, in
dimension-name order (`HOUR*MONEY/KWH`, `KWH/HOUR`, `1/DAY`). `parse_unit`
accepts a text only when it is exactly that canonical text.

`QUANTITY_UNITS` and `BAND_UNITS` are the only bridge from record units to
catalogue units (R10): readers use them and write no mapping of their own.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType

DIMENSIONS = ("DAY", "HOUR", "KWH", "L", "MINUTE", "MONEY")

_DIM = "(?:DAY|HOUR|KWH|L|MINUTE|MONEY)"
_UNIT_TEXT = re.compile(rf"(?:1|{_DIM}(?:\*{_DIM})*)(?:/{_DIM}(?:\*{_DIM})*)?", re.ASCII)


def _normalise(exponents: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((d, e) for d, e in exponents.items() if e != 0))


@dataclass(frozen=True)
class Unit:
    """A product of dimension powers; `exponents` sorted by name, zeros dropped."""

    exponents: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        for dimension, _ in self.exponents:
            if dimension not in DIMENSIONS:
                raise ValueError(f"CANONICAL_UNIT {dimension}")
        object.__setattr__(self, "exponents", _normalise(dict(self.exponents)))

    def _combine(self, other: "Unit", sign: int) -> "Unit":
        if not isinstance(other, Unit):
            return NotImplemented
        merged = dict(self.exponents)
        for dimension, exponent in other.exponents:
            merged[dimension] = merged.get(dimension, 0) + sign * exponent
        return Unit(_normalise(merged))

    def __mul__(self, other: "Unit") -> "Unit":
        return self._combine(other, 1)

    def __truediv__(self, other: "Unit") -> "Unit":
        return self._combine(other, -1)

    @property
    def is_money(self) -> bool:
        """True only for exactly `MONEY^1`."""
        return self.exponents == (("MONEY", 1),)

    @property
    def has_money_dimension(self) -> bool:
        """True when `MONEY` appears at any non-zero exponent (`MONEY`, `MONEY/KWH`, `MONEY/L`): the unit needs a
        currency. The one shared rule (D-DS4.27); `is_money` stays exactly `MONEY^1`."""
        return any(d == "MONEY" and e != 0 for d, e in self.exponents)

    def __str__(self) -> str:
        if not self.exponents:
            return "1"
        numerator = [d for d, e in self.exponents if e > 0 for _ in range(e)]
        denominator = [d for d, e in self.exponents if e < 0 for _ in range(-e)]
        text = "*".join(numerator) if numerator else "1"
        if denominator:
            text += "/" + "*".join(denominator)
        return text


def parse_unit(text: str) -> Unit:
    """The `Unit` of a canonical unit text; any other text raises `ValueError`."""
    if not isinstance(text, str) or _UNIT_TEXT.fullmatch(text) is None:
        raise ValueError(f"CANONICAL_UNIT {text}")
    numerator, _, denominator = text.partition("/")
    exponents: dict[str, int] = {}
    if numerator != "1":
        for dimension in numerator.split("*"):
            exponents[dimension] = exponents.get(dimension, 0) + 1
    if denominator:
        for dimension in denominator.split("*"):
            exponents[dimension] = exponents.get(dimension, 0) - 1
    unit = Unit(_normalise(exponents))
    if str(unit) != text:
        raise ValueError(f"CANONICAL_UNIT {text}")
    return unit


ONE = Unit()
KWH = Unit((("KWH", 1),))
L = Unit((("L", 1),))
MONEY = Unit((("MONEY", 1),))
DAY = Unit((("DAY", 1),))
HOUR = Unit((("HOUR", 1),))
MINUTE = Unit((("MINUTE", 1),))
KW = KWH / HOUR

QUANTITY_UNITS = MappingProxyType({
    "kWh": KWH,
    "kW": KW,
    "L": L,
    "crate": ONE,
    "crate_day": DAY,
})

BAND_UNITS = MappingProxyType({
    "per_kWh": MONEY / KWH,
    "per_crate_day": MONEY / DAY,
    "per_L": MONEY / L,
})
