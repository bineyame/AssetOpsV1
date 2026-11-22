"""6a (`specs/6a-decision-records/spec.md` §3.1; D-P6.2, D-P6.12, D-P6.23): the levers a factor's change may act on.

A lever is a code row: the factor whose change is its purpose, the settings it varies (a grid along named axes) and
the leaves an option of it changes by a delta (6c). `check.check_levers` refuses a bad lever at start-up. This
module is pure: it imports only `decimal`, `dataclasses`, `types` and `collections.abc`.
"""
from decimal import Decimal
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping


@dataclass(frozen=True)
class SettingAxis:
    name: str                       # ID_RE; e.g. "stop_soc_pct"
    values: tuple[Decimal, ...]     # the grid along this axis, in the order tried; whole numbers for a key template
    unit: str                       # "%"


@dataclass(frozen=True)
class Lever:
    lever_id: str
    structure_key: str              # a key of REGISTRIES
    purpose_factor: str             # a row of that registry: the factor whose change is the lever's purpose
    generator: str                  # "SETTING_GRID" (the only generator in 6a)
    axes: tuple[SettingAxis, ...]
    key_template: str               # e.g. "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}"
    changes: tuple[str, ...]        # the leaves an option of this lever changes by a delta (6c; D-P6.3)


LEVERS: Mapping[str, Lever] = MappingProxyType({
    "generator_stop_reserve": Lever(
        "generator_stop_reserve", "MINI_GRID", "candidate_l", "SETTING_GRID",
        (SettingAxis("stop_soc_pct", tuple(Decimal(v) for v in (90, 85, 80, 75, 70, 65, 60)), "%"),
         SettingAxis("reserve_soc_pct", (Decimal(30), Decimal(25)), "%")),
        "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}",
        ("candidate_l", "battery_throughput_kwh")),
})


def grid(lever: Lever) -> tuple[Mapping[str, Decimal], ...]:
    """Every point of the lever's grid, first axis outermost, each axis in `values` order."""
    points: list[dict[str, Decimal]] = [{}]
    for axis in lever.axes:
        points = [{**point, axis.name: value} for point in points for value in axis.values]
    return tuple(MappingProxyType(point) for point in points)


def option_key(lever: Lever, point: Mapping[str, Decimal]) -> str:
    """The template filled with `format(v, "f")` of each whole value (a non-whole value is refused at start-up)."""
    return lever.key_template.format(**{name: format(value, "f") for name, value in point.items()})
