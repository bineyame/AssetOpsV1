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


def _named(lever_id: str, structure_key: str, purpose_factor: str, sources: dict[str, ChangeSource],
           options: tuple[tuple[str, str, tuple[str, ...]], ...], *, bounds_required: bool = False,
           no_action_words: str = "KEEP") -> Lever:
    """A STATED_OPTIONS lever: `changes` are the source keys in the order written (registry order)."""
    return Lever(lever_id, structure_key, purpose_factor, "STATED_OPTIONS", (), "", tuple(sources),
                 options=tuple(LeverOption(key, kind, changes) for key, kind, changes in options),
                 change_sources=MappingProxyType(dict(sources)), bounds_required=bounds_required,
                 no_action_words=no_action_words)


_EV_SCHEDULE = ("peak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw", "extra_missed_departures")

LEVERS: Mapping[str, Lever] = MappingProxyType({
    "generator_stop_reserve": Lever(
        "generator_stop_reserve", "MINI_GRID", "candidate_l", "SETTING_GRID",
        (SettingAxis("stop_soc_pct", tuple(Decimal(v) for v in (90, 85, 80, 75, 70, 65, 60)), "%"),
         SettingAxis("reserve_soc_pct", (Decimal(30), Decimal(25)), "%")),
        "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}",
        ("candidate_l", "battery_throughput_kwh"),
        change_sources=MappingProxyType({"candidate_l": STUDY, "battery_throughput_kwh": STUDY}),
        no_action_words="KEEP_SETTINGS"),
    # 6h (spec §5.1; D-P6.55, D-P6.57, D-P6.59): the named-option levers, every one STATED_OPTIONS
    **{lever.lever_id: lever for lever in (
        _named("backup_cover", "COLD_CHAIN", "nights_without_backup_cover", {"uncovered_nights": RECORD},
               (("stopgap-and-claim", "SUPPLIER_REMEDY", ("uncovered_nights",)),
                ("self-repair", "REPAIR", ("uncovered_nights",))),
               bounds_required=True, no_action_words="WAIT_FOR_REMEDY"),
        _named("chamber_efficiency", "COLD_CHAIN", "excess_kwh", {"model_factor": RECORD, "excess_kwh": RECORD},
               (("repair", "REPAIR", ("excess_kwh",)),
                ("replace", "CAPEX", ("model_factor", "excess_kwh")))),
        _named("storage_contract", "COLD_CHAIN", "contract_crate_days",
               {"contract_crate_days": RECORD, "contract_rate": RECORD, "handling": RECORD},
               (("storage-contract", "DEMAND_CONTRACT", ("contract_crate_days", "contract_rate", "handling")),)),
        _named("charging_schedule", "EV_DEPOT_CAPTIVE", "peak_kwh",
               {"peak_kwh": STUDY, "kwh_2200_2400": STUDY, "kwh_0000_0500": STUDY, "max_kw": STUDY,
                "extra_missed_departures": STUDY},
               (("deadline-aware", "SCHEDULE", _EV_SCHEDULE), ("cheapest-window", "SCHEDULE", _EV_SCHEDULE))),
        _named("charger_restore", "EV_DEPOT_CAPTIVE", "departures_missed",
               {"covered_bus_nights": RECORD, "extra_missed_departures": RECORD},
               (("stopgap-and-claim", "SUPPLIER_REMEDY", ("covered_bus_nights",)),
                ("local-repair", "REPAIR", ("extra_missed_departures",)),
                ("reschedule", "SCHEDULE", ("extra_missed_departures",))),
               bounds_required=True, no_action_words="WAIT_FOR_REMEDY"),
        _named("fleet_capacity_use", "EV_DEPOT_CAPTIVE", "buses", {"buses": RECORD},
               (("absorb-part", "CAPACITY_USE", ("buses",)), ("absorb-all", "CAPACITY_USE", ("buses",)),
                ("add-chargers", "CAPEX", ("buses",)))),
        _named("generator_redundancy", "MINI_GRID", "obligation_hours_without_redundancy", {"reduced_days": RECORD},
               (("repair", "REPAIR", ("reduced_days",)), ("replace", "CAPEX", ("reduced_days",)),
                ("add-storage", "CAPEX", ("reduced_days",))),
               bounds_required=True),
        _named("productive_demand", "MINI_GRID", "productive_kwh", {"productive_kwh": RECORD},
               (("new-connection", "DEMAND_CONNECTION", ("productive_kwh",)),)),
        _named("fuel_reconciliation", "MINI_GRID", "unexplained_l", {"unexplained_l": RECORD},
               (("investigate", "INVESTIGATION", ("unexplained_l",)),)),
    )},
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
