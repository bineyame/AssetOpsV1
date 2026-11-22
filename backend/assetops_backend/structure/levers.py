"""6a (`specs/6a-decision-records/spec.md` §3.1; D-P6.2, D-P6.12, D-P6.23): the levers a factor's change may act on.

A lever is a code row: the factor whose change is its purpose, the settings it varies (a grid along named axes) and
the leaves an option of it changes by a delta (6c). `check.check_levers` refuses a bad lever at start-up.

6h added the second generator, `STATED_OPTIONS` (spec §3.1): a lever lists named options, each with the leaves it
moves, and each changed leaf names its source (`STUDY` or `RECORD`). This module is pure: it imports only `decimal`,
`dataclasses`, `types` and `collections.abc`.
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
class LeverOption:
    """6h (spec §3.1): a named option of a `STATED_OPTIONS` lever and the leaves it moves."""
    key: str                        # _OPTION_KEY; never "no-action"
    kind: str                       # OPTION_KINDS
    changes: tuple[str, ...]        # non-empty subset of Lever.changes, in Lever.changes order


@dataclass(frozen=True)
class ChangeSource:
    """6h (spec §3.1): where a changed leaf's level comes from: a replay of the Site's own month, or a document."""
    kind: str                       # "STUDY" | "RECORD"


OPTION_KINDS = ("REPAIR", "CAPEX", "SUPPLIER_REMEDY", "SCHEDULE", "DEMAND_CONTRACT", "CAPACITY_USE",
                "DEMAND_CONNECTION", "INVESTIGATION")
GENERATORS = ("SETTING_GRID", "STATED_OPTIONS")
CHANGE_SOURCE_KINDS = ("STUDY", "RECORD")
NO_ACTION_WORDS = ("KEEP_SETTINGS", "KEEP", "WAIT_FOR_REMEDY")   # how doing nothing reads (6f, D-P6.58, D-P6.66 N1)
STUDY = ChangeSource("STUDY")
RECORD = ChangeSource("RECORD")


@dataclass(frozen=True)
class Lever:
    lever_id: str
    structure_key: str              # a key of REGISTRIES
    purpose_factor: str             # a row of that registry: the factor whose change is the lever's purpose
    generator: str                  # GENERATORS
    axes: tuple[SettingAxis, ...]
    key_template: str               # e.g. "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}"
    changes: tuple[str, ...]        # the leaves an option of this lever changes by a delta (6c; D-P6.3)
    options: tuple[LeverOption, ...] = ()                                  # 6h: STATED_OPTIONS only
    change_sources: Mapping[str, ChangeSource] = MappingProxyType({})      # 6h: one per changed leaf
    bounds_required: bool = False   # D-P6.57: a protective lever; no recommendation until 6b's bounds
    no_action_words: str = "KEEP"   # NO_ACTION_WORDS


LEVERS: Mapping[str, Lever] = MappingProxyType({
    "generator_stop_reserve": Lever(
        "generator_stop_reserve", "MINI_GRID", "candidate_l", "SETTING_GRID",
        (SettingAxis("stop_soc_pct", tuple(Decimal(v) for v in (90, 85, 80, 75, 70, 65, 60)), "%"),
         SettingAxis("reserve_soc_pct", (Decimal(30), Decimal(25)), "%")),
        "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}",
        ("candidate_l", "battery_throughput_kwh"),
        change_sources=MappingProxyType({"candidate_l": STUDY, "battery_throughput_kwh": STUDY}),
        no_action_words="KEEP_SETTINGS"),
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
