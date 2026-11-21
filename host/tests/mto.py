"""0M: the Mto plant and its declared simulated season (spec §3; D-0M.2, D-0M.3, D-0M.20, D-0M.21).

A test fixture, never a record. Mto's base in the manifest (`hybrid-mini-grid-100kw`) lacks the properties the
mini-grid models v5-v7 resolve, so the plant is the Kobo template edited to the manifest's Mto `physical` facts
(PV 50 kW, battery 150 kWh, reserve 30 %, generator 30 kW, SFC 0.33 L/kWh) and the inverter limit: 50 kW for
INV-MT-01 and INV-MT-02 together (the kernel models one AC limit), 25 kW with INV-MT-02 failed. Facts Mto does not
state keep the template's values (the packet lists them). The season is Kobo's day types and calendar
(`kobo_season.py`) with every load x 1/2: Mto delivered 6,000 kWh in October against the Kobo profile's about 11,580
a month (6,000 / 11,580 ~ 0.52, declared 1/2; the only derivation, D-0M.21). The site keeps the template fixture's
`KOBO-001` id; results carry the run id, never a Site name.
"""

from __future__ import annotations

from datetime import time
from fractions import Fraction

from assetops_backend.runs.headroom_replay import CustomerLoad
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.replay_study import StudyFrame
from assetops_contracts.world_inputs import FrozenWorldInputs

from kobo import component, set_property
from kobo_assumed import ASSUMED_BASIS, ASSUMED_DERIVATION, ASSUMED_PROPERTIES
from kobo_season import TIMEZONE, base_run, season_inputs, season_site

#: (component, property, value): document numbers, the manifest's Mto `physical` line
#: (`pv_kw: 50, battery_kwh: 150, reserve_soc_pct: 30, genset_kw: 30, sfc_l_per_kwh: 0.33`).
MTO_FACTS = (("pv-array", "pv-rated-power", 50), ("battery", "battery-energy-capacity", 150),
             ("battery", "reserve-state-of-charge", 30), ("generator", "generator-rated-power", 30),
             ("generator", "specific-fuel-consumption", 0.33))
MTO_RATINGS = (("pv-array", 50), ("battery", 150), ("generator", 30))  # each component's `rating.value`
MTO_INVERTER_KW = Fraction(50)  # INV-MT-01 25 kW + INV-MT-02 25 kW, one AC limit
MTO_REDUCED_INVERTER_KW = Fraction(25)  # INV-MT-02 failed 28 Oct
MTO_LOAD_SCALE = Fraction(1, 2)  # Mto delivered 6,000 kWh in October; the Kobo profile is about 11,580 a month
#                                  (6,000 / 11,580 ~ 0.52, declared 1/2: the only derivation, D-0M.21)
MTO_PLANT_NOTE = "Kobo template edited to Mto's manifest facts; loads halved; simulated season"  # D-0M.14


def _document_number(value: Fraction) -> int:
    if value.denominator != 1:
        raise ValueError(f"an inverter limit of {value} kW is not a whole document number")
    return value.numerator


def mto_site(inverter_limit_kw: Fraction = MTO_INVERTER_KW):
    """A `site_edit` for `kobo_draft`: the season's Foundation first, then Mto's facts and the inverter limit."""
    limit = _document_number(inverter_limit_kw)

    def edit(document) -> None:
        season_site(document)  # FIRST: without the season's valid_from the run is BLOCKED (D-0M.20)
        for component_id, key, value in MTO_FACTS:
            set_property(document, component_id, key, value)
        for component_id, value in MTO_RATINGS:
            component(document, component_id)["rating"]["value"] = value
        set_property(document, "pv-inverter", "inverter-ac-limit", limit)
        component(document, "pv-inverter")["rating"]["value"] = limit

    return edit


#: 0K4d (D-0K4.27): the values Mto has not sent, assumed for `mini-grid` v8 runs, each with its basis row. The
#: no-load rate is the generic rule of 0.08 L/h per kW of rating x Mto's 30 kW, never scaled from Kobo's 3.3 (the
#: owner's value for one set); minimum load and taper start are Kobo's assumed rows unchanged.
MTO_ASSUMED: dict[str, tuple[tuple[str, object, str], ...]] = {
    "generator": (
        ("generator-no-load-fuel-rate", 2.4, "L/h"),
        ("generator-no-load-fuel-rate-basis", ASSUMED_BASIS, "state"),
        ("generator-minimum-load", 30, "%"),
        ("generator-minimum-load-basis", ASSUMED_BASIS, "state"),
    ),
    "battery": ASSUMED_PROPERTIES["battery"],
}
#: (label, basis, derivation) per assumed or declared key, worded as D-0K4.27; a key with no entry is `KeyError`.
MTO_ASSUMED_DERIVATION: dict[str, tuple[str, str, str]] = {
    "generator-no-load-fuel-rate": (
        "assumed", "GENERIC_DEFAULT", "the generic rule of 0.08 L/h per kW of rating x 30 kW; no owner value for Mto"),
    "generator-minimum-load": ASSUMED_DERIVATION["generator-minimum-load"],
    "battery-charge-taper-start": ASSUMED_DERIVATION["battery-charge-taper-start"],
    "specific-fuel-consumption": (
        "declared", "MANIFEST", "Mto's physical line, read as consumption at rated output"),
}


def mto_site_v2(inverter_limit_kw: Fraction = MTO_INVERTER_KW):
    """`mto_site` then `MTO_ASSUMED` appended, as `assumed_site` does with Kobo's; a key present is `KeyError`."""
    base = mto_site(inverter_limit_kw)

    def edit(document) -> None:
        base(document)
        for component_id, rows in MTO_ASSUMED.items():
            item = component(document, component_id)
            properties = item.get("properties") or []
            present = {entry["property_key"] for entry in properties}
            for key, value, unit in rows:
                if key in present:
                    raise KeyError(f"{key} is already declared on {component_id}")
                properties.append(
                    {"property_key": key, "value": value, "unit": unit, "source": "SITE", "source_version": 1})
            item["properties"] = properties

    return edit


def mto_base_run(days: int, *, inverter_limit_kw: Fraction = MTO_INVERTER_KW, version: int = 7,
                 site=mto_site) -> SimulationRun:
    return base_run(days, site_edit=site(inverter_limit_kw), version=version)


def mto_season(run, days, season: str = "v1") -> FrozenWorldInputs:
    return season_inputs(run, days, load_scale=MTO_LOAD_SCALE, season=season)


#: MTO-HULLER: 15 kW, 10:00-15:00, 22 days a month (Monday to Friday local, D-0M.5), signed letter of intent.
HULLER = CustomerLoad("mto-huller", Fraction(15), time(10), time(15), frozenset(range(5)), "load-mill", "SIGNED")
#: MTO-WELDING: 10 kW, 18:00-21:00, 22 days a month, verbal enquiry (the negative control, D-0M.9).
WELDER = CustomerLoad("mto-welder", Fraction(10), time(18), time(21), frozenset(range(5)), "load-mill", "VERBAL")
MTO_FRAME = StudyFrame(timezone=TIMEZONE, battery_capacity_kwh=Fraction(150))

__all__ = [
    "HULLER",
    "MTO_ASSUMED",
    "MTO_ASSUMED_DERIVATION",
    "MTO_FACTS",
    "MTO_FRAME",
    "MTO_INVERTER_KW",
    "MTO_LOAD_SCALE",
    "MTO_PLANT_NOTE",
    "MTO_RATINGS",
    "MTO_REDUCED_INVERTER_KW",
    "WELDER",
    "mto_base_run",
    "mto_season",
    "mto_site",
    "mto_site_v2",
]
