"""DD3.1 (spec `specs/DD-demo-data/spec.md` §4.1, §4.2; D-DD.19, D-DD.28, D-DD.69, D-DD.71, D-DD.72): the telemetry writer.

Pure: no store, clock, network or randomness. It reads a Site's foundation and bindings (`F`, the
`assetops.world-site-inputs/1` file), the decided books (delivered kWh and unexplained litres per month, the fuel
notes) and the manifest view, and writes one readings file per Site-day.

**One continuous execution per Site, advanced one local day at a time (D-DD.69).** The Site's pack execution starts
at the span's first local midnight from the declared initial state and is advanced 288 five-minute steps per day;
each day's readings come from that day's steps, so day d+1 starts from day d's end state, a RUNNING generator
included.

**Inputs the readings follow.** Load is the declared hourly shape (`LOAD_SHAPE_KW`) times the `demand` family's day
weight, scaled by largest remainder so a month's load energy equals the month's `delivered_kwh` exactly
(`TEL_INPUT_TOTAL` otherwise). Sun is `SUN_W_PER_M2`: at `SEASON_V2_SUN_SITES` season v2's clear or overcast day on
its calendar (1 Sep to the last day of Oct), any other day or Site the clear shape times the `solar_surplus` day
weight, season x day class (D-DD.77, D-DD.129). The pack is v8 for one generator and one inverter, else v9, with each
unit answered and attached and `UNIT_EVENTS` as one-minute forcings (D-DD.126, D-DD.129, D-DD.145); the starting
state of charge comes from one warm-up day (D-DD.104). Deliveries are tank INCREASE points
at each note's instant; the unexplained draw is a tank DECREASE point of the month's `unexplained_l`, in equal daily
parts at 02:00 local, largest remainder to 0.01 L. The tank starts at 50 % of its capacity. Each is written in the
readings manifest's `conditions`; the story's answer block is never read (`TEL_ORACLE_READ`).

**The foundation to the pack.** `NEEDS` is this module's own table of property to address; it duplicates the
backend's (`runs/profiles.py`, `host/execution_adapter.py`) because a simulator module cannot import the backend.
`tools/dd_check.py` clause `C-DD21` compares the two so a drift fails.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

from assetops_contracts.execution_contract import EXECUTION_CONTRACT_VERSION
from assetops_contracts.world_inputs import (
    BusAttachmentInput,
    DeclaredBound,
    DeclaredCause,
    DiscreteInitialValue,
    ForcingInput,
    FrozenInterval,
    FrozenWorldInputs,
    InitialValue,
    SiteControlInput,
)

from ..kernel.execute import start as start_execution
from ..packs import generator_curve
from ..packs.mini_grid import MINI_GRID_V8_MODEL, MINI_GRID_V9_MODEL
from . import GENERATOR
from .allocate import allocate
from .canonical import canonical_bytes, file_bytes, sha256_hex
from .months import day_class, parse_month

SITE_INPUTS_SCHEMA = "assetops.world-site-inputs/1"
READINGS_SCHEMA = "assetops.world-readings/1"
MANIFEST_SCHEMA = "assetops.world-readings-manifest/1"
#: D-DD.103: the readings span, local time, declared once. The mini-grid, cold and EV writers, the CLI defaults and
#: DD5's world manifest `span` read it. The execution horizon ends at the end instant (no step after 06:00 on 6 Nov).
READINGS_SPAN = ("2026-07-01T00:00", "2026-11-06T06:00")
STEP_MINUTES = 5
STEPS_PER_DAY = 288
HOURS_PER_STEP = Fraction(STEP_MINUTES, 60)
TANK_START_FRACTION = Fraction(1, 2)  # D-DD.19: Assumed, declared in the manifest's conditions
DRAW_MINUTE = 120  # 02:00 local
QUANTUM = Decimal("0.001")  # a reading is written to the millesimal, half-even; exact decimal text

#: The packs the writer drives (D-DD.129): v8 where a Site has one generator and one inverter, v9 otherwise.
MODELS = {8: MINI_GRID_V8_MODEL, 9: MINI_GRID_V9_MODEL}
#: The unit kinds: a Site may have several, each answered per unit (`Need.per_unit`); the lead is the first by code.
UNIT_KINDS = ("GENERATOR", "INVERTER")

#: Guards against a read of the story's answer key. The writer's own source must not name it (`C-DD12`).
ORACLE_KEY = "orac" + "le"


class TelemetryRefused(ValueError):
    """`<CODE> <detail>` (spec §4.1 refusals)."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code} {detail}")
        self.code = code


def refuse_oracle(document: object, path: str = "$") -> None:
    """`TEL_ORACLE_READ`: a key of the answer block anywhere in an input document."""
    if isinstance(document, dict):
        for key, value in document.items():
            if key == ORACLE_KEY:
                raise TelemetryRefused("TEL_ORACLE_READ", path)
            refuse_oracle(value, f"{path}.{key}")
    elif isinstance(document, list):
        for index, item in enumerate(document):
            refuse_oracle(item, f"{path}[{index}]")


# --- the foundation to the pack ---------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Need:
    state_key: str
    component_type: str
    property_key: str
    unit: str  # the canonical unit the kernel reads
    dimension: str
    source_unit: str  # the unit the property is declared in
    divisor: int = 1  # canonical = declared / divisor (L/h to L/min)
    per_unit: bool = False  # D-DD.129: answered for every unit of its kind; otherwise the lead unit's (D-DD.43)
    version: int | None = None  # a need only this pack version reads (None: every version)


#: The initial values a Site's foundation answers, in the order the backend freezes them. Parity: `C-DD21`.
NEEDS: tuple[Need, ...] = (
    Need("pv-rated-power", "PV_ARRAY", "pv-rated-power", "kW", "POWER", "kW"),
    Need("inverter-ac-limit", "INVERTER", "inverter-ac-limit", "kW", "POWER", "kW", per_unit=True),
    Need("battery-energy-capacity", "BATTERY", "battery-energy-capacity", "kWh", "ENERGY", "kWh"),
    Need("pcs-charge-limit", "POWER_CONVERSION_SYSTEM", "pcs-charge-limit", "kW", "POWER", "kW"),
    Need("pcs-discharge-limit", "POWER_CONVERSION_SYSTEM", "pcs-discharge-limit", "kW", "POWER", "kW"),
    Need("pcs-conversion-efficiency", "POWER_CONVERSION_SYSTEM", "pcs-conversion-efficiency", "%", "FRACTION", "%"),
    Need("battery-reserve-state-of-charge", "BATTERY", "reserve-state-of-charge", "%", "FRACTION", "%"),
    Need("generator-rated-power", "GENERATOR", "generator-rated-power", "kW", "POWER", "kW", per_unit=True),
    Need("generator-specific-fuel-consumption", "GENERATOR", "specific-fuel-consumption", "L/kWh",
         "VOLUME_PER_ENERGY", "L/kWh", per_unit=True),
    Need("generator-start-soc-threshold", "GENERATOR", "start-soc-threshold", "%", "FRACTION", "%"),
    Need("generator-stop-soc-threshold", "GENERATOR", "stop-soc-threshold", "%", "FRACTION", "%"),
    Need("generator-minimum-runtime", "GENERATOR", "minimum-runtime", "min", "DURATION", "min"),
    Need("generator-start-delay", "GENERATOR", "start-delay", "min", "DURATION", "min"),
    Need("fuel-tank-capacity", "FUEL_TANK", "tank-capacity", "L", "VOLUME", "L"),
    Need("generator-no-load-fuel-rate", "GENERATOR", "generator-no-load-fuel-rate", "L/min", "VOLUME_RATE", "L/h", 60,
         per_unit=True),
    Need("generator-minimum-load", "GENERATOR", "generator-minimum-load", "%", "FRACTION", "%", per_unit=True),
    Need("battery-charge-taper-start", "BATTERY", "battery-charge-taper-start", "%", "FRACTION", "%"),
    # D-DD.128/129: v9 only; declared in %, read as a fraction (the pack checks 0 < share and that the shares sum to 1)
    Need("pv-array-share", "INVERTER", "pv-array-share", "1", "FRACTION", "%", 100, per_unit=True, version=9),
)
SOC_ADDRESS = "battery-state-of-charge"
TANK_ADDRESS = "fuel-tank-volume"
STATE_ADDRESS = "generator-state"
IRRADIANCE = "site:plane-of-array-irradiance"


def _text(value: object) -> str:
    """A declared number as the text its author wrote (floats by `repr`, never as binary floats)."""
    if isinstance(value, bool):
        raise ValueError("a property value is a number")
    if isinstance(value, float):
        return repr(value)
    return str(value)


def site_inputs(onboarding: dict, bindings: dict[str, dict]) -> dict:
    """`F` (D-DD.28): each `/2` Site joined with its binding conversion, sorted by Site code. Pure."""
    refuse_oracle(onboarding)
    operator = onboarding["operator"]["slug"]
    sites, unbound = [], []
    for site in sorted(onboarding["sites"], key=lambda s: s["code"]):
        binding = bindings.get(site["code"])
        if binding is None:  # D-DD.129: listed, and written as a `not_written` manifest line, never skipped
            unbound.append({"tenant": operator, "code": site["code"]})
            continue
        components = [
            {"id": c["id"], "type": c["type"],
             **({"rating": {"value": _text(c["rating"]["value"]), "unit": c["rating"]["unit"]}} if c.get("rating") else {}),
             "properties": [{"property_key": p["property_key"], "value": _text(p["value"]), "unit": p["unit"]}
                            for p in c.get("properties", [])]}  # D-DD.95: a rating is written only when the component has one
            for c in site["components"]]
        foundation = {"components": components, "devices": site.get("devices", []), "topology": site["topology"]}
        rows = [{"device_id": b["device_id"], "signal_id": b["signal_id"], "role": b["role"], "asset_code": b["asset_code"],
                 "source_unit": b["source_unit"], "canonical_unit": b["canonical_unit"], "conversion": b["conversion"]}
                for b in binding["bindings"]]
        sites.append({
            "tenant": operator, "code": site["code"], "timezone": site["timezone"], "valid_from": site["valid_from"],
            "foundation": foundation, "role_set": binding["role_set"], "bindings": rows,
            "foundation_digest": sha256_hex(canonical_bytes({"foundation": foundation, "bindings": rows,
                                                             "role_set": binding["role_set"]}))})
    return {"schema": SITE_INPUTS_SCHEMA, "generator": GENERATOR, "sites": sites, **({"unbound": unbound} if unbound else {})}


# --- inputs: shapes, scaling, the frozen record ------------------------------------------------------------------------

#: The declared load shape (kW at each local hour, one shape at every Site; season v2's blocks of
#: `host/tests/kobo_season.py` read hour by hour, the residential evening block from dark, D-DD.97). Written in the
#: manifest's `conditions`.
LOAD_SHAPE_KW: dict[str, tuple[int, ...]] = {
    "clinic": (2, 2, 2, 2, 2, 2, 5, 5, 6, 6, 7, 7, 7, 7, 6, 6, 5, 5, 5, 5, 4, 4, 2, 2),
    "mill": (0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 18, 18, 10, 10, 12, 12, 0, 0, 0, 0, 0, 0, 0, 0),
    "res": (5, 5, 3, 3, 3, 5, 8, 8, 6, 6, 5, 5, 6, 6, 8, 8, 8, 8, 14, 14, 14, 14, 9, 9),
}
LOAD_SHAPE_BASIS = ("residential evening use from dark (18:00 local); Assumed from measured East-African mini-grid "
                    "profiles")
#: Plane-of-array irradiance (W/m2) at each local hour, a clear and an overcast day.
SUN_W_PER_M2: dict[str, tuple[int, ...]] = {
    "clear": (0, 0, 0, 0, 0, 0, 150, 150, 550, 550, 900, 900, 950, 950, 600, 600, 150, 150, 0, 0, 0, 0, 0, 0),
    "overcast": (0, 0, 0, 0, 0, 0, 50, 50, 190, 190, 310, 310, 330, 330, 210, 210, 50, 50, 0, 0, 0, 0, 0, 0),
}
#: Season v2's overcast days, indexed from 2026-09-01 (`host/tests/kobo_season.py` OVERCAST_V2); no other day is.
OVERCAST_DAYS = frozenset({2, 3, 7, 8, 9, 13, 17, 18, 19, 20, 24, 25, 28, 33, 38, 39, 45, 50, 51, 52, 57})
SEASON_V2_DAY_ZERO = date(2026, 9, 1)
SEASON_V2_DAYS = 61  # D-0K2.1's calendar length: 1 Sep to the end of Oct (host test pins it to kobo_season.SEASON_DAYS)
SEASON_V2_LAST_DAY = SEASON_V2_DAY_ZERO + timedelta(days=SEASON_V2_DAYS - 1)
#: D-DD.129: the Sites whose sun follows season v2's calendar (spec §4.2, D-DD.77); every other Site's every day is
#: the clear shape times the `solar_surplus` weight.
SEASON_V2_SUN_SITES = ("KOBO-001",)
#: D-DD.77: the `solar_surplus` family of the manifest's `history` block (pinned to it by `test_scope_seasons_parity`).
#: Not a writer default (D-DD.129: the books' `sun_weights` is required); tests' hand-made books carry it.
#: A day outside season v2's calendar gets the clear shape times season x day-class weight, no jitter.
DEFAULT_SUN_WEIGHTS = {
    "seasons": {"2026-07": "cool_dry", "2026-08": "cool_dry", "2026-09": "warm_dry", "2026-10": "short_rains",
                "2026-11": "short_rains"},
    "classes": {"WD": [1, 2, 3, 4, 5], "SA": [6], "SU": [7]},
    "season": {"cool_dry": "0.80", "warm_dry": "1.10", "short_rains": "1.00"},
    "day": {"WD": "1.00", "SA": "1.00", "SU": "1.00"}}
SUN_RULE = "clear shape x solar_surplus day weight (season x day class, no jitter) (D-DD.77)"
#: Critical-load order (clinic first), by the load component's id; others follow by id.
CRITICAL_ORDER = ("clinic", "res", "mill")

#: D-DD.126: the unit failures and restores of `M` `operations` (instant, local), parity-tested against it (D-DD.51).
#: Each is a one-minute WINDOW forcing at its instant, read at the step that holds it (D-DD.145).
UNIT_EVENTS: tuple[dict[str, str], ...] = (
    {"site": "KISIWA-001", "unit": "gen-ks-01", "kind": "unit-fail", "at": "2026-08-14T19:20+03:00",
     "source": "kis-gen1-2026-08-14"},
    {"site": "KISIWA-001", "unit": "gen-ks-01", "kind": "unit-restore", "at": "2026-08-17T11:00+03:00",
     "source": "kis-gen1-2026-08-14"},
    {"site": "KISIWA-001", "unit": "gen-ks-01", "kind": "unit-fail", "at": "2026-10-30T18:40+03:00",
     "source": "kis-gen1-2026-10-30"},
    {"site": "MTO-001", "unit": "inv-mt-02", "kind": "unit-fail", "at": "2026-10-28T11:02+03:00",
     "source": "mto-inv2-2026-10-28"},
)
UNIT_EVENT_TIMING = ("unit failures and restores apply at the 5-minute step holding their instant; the controller "
                     "responds at the next step (Assumed)")
START_SOC_BASIS = ("Derived: the 00:00 state after one warm-up day of the span's first day from the declared stop "
                   "threshold (D-DD.104)")


def _feeder(component_id: str) -> str:
    for name in CRITICAL_ORDER:
        if name in component_id:
            return name
    raise TelemetryRefused("TEL_FOUNDATION", f"{component_id} is a load with no declared shape")


def _zone(site: dict) -> ZoneInfo:
    return ZoneInfo(site["timezone"])


def _utc(zone: ZoneInfo, day: date, minute: int = 0) -> datetime:
    return (datetime(day.year, day.month, day.day, tzinfo=zone) + timedelta(minutes=minute)).astimezone(timezone.utc)


def _iso_utc(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def span_days(first: str, last: str) -> tuple[list[date], int]:
    """The local days of the span and the end instant's minute in the last one (1440: the whole day; D-DD.103).
    `first` is a local date or its midnight (`YYYY-MM-DDT00:00`); `last` a local date (the whole day) or a local
    instant `YYYY-MM-DDTHH:MM` on a whole hour (a midnight ends the day before)."""
    if len(first) > 10 and first[10:] not in ("T00:00", "T00:00:00"):
        raise TelemetryRefused("TEL_EVENT_UNPLACED", f"the span starts at {first}, not at a local midnight")
    start = date.fromisoformat(first[:10])
    if len(last) > 10:
        moment = datetime.fromisoformat(last)
        if moment.tzinfo is not None or moment.second or moment.microsecond or moment.minute:
            raise TelemetryRefused("TEL_EVENT_UNPLACED", f"the span end {last} is not a local whole hour")
        end, minute = moment.date(), moment.hour * 60
        if minute == 0:
            end, minute = end - timedelta(days=1), 1440
    else:
        end, minute = date.fromisoformat(last), 1440
    if end < start:
        raise TelemetryRefused("TEL_EVENT_UNPLACED", f"the span {first}..{last} is empty")
    return [start + timedelta(days=i) for i in range((end - start).days + 1)], minute


def _days(first: str, last: str) -> list[date]:
    return span_days(first, last)[0]


def _span_hours(day: date) -> range:
    """The local hours of `day` inside `READINGS_SPAN` (empty outside it)."""
    days, minute = span_days(*READINGS_SPAN)
    if not days[0] <= day <= days[-1]:
        return range(0)
    return range(minute // 60) if day == days[-1] else range(24)


def _component(foundation: dict, kind: str, code: str) -> dict:
    """The one component of a single-cardinality kind (a unit kind has its lead, `_units`)."""
    found = [c for c in foundation["components"] if c["type"] == kind]
    if kind in UNIT_KINDS:
        return _units(foundation, kind, code)[0]
    if len(found) != 1:
        raise TelemetryRefused("TEL_FOUNDATION", f"{code} needs exactly one {kind}, has {len(found)}")
    return found[0]


def _units(foundation: dict, kind: str, code: str) -> list[dict]:
    """A unit kind's components in code order (the pack's declared order, spec §4.3); the first is the lead."""
    found = sorted((c for c in foundation["components"] if c["type"] == kind), key=lambda c: c["id"])
    if not found:
        raise TelemetryRefused("TEL_FOUNDATION", f"{code} needs at least one {kind}")
    return found


def pack_version(site: dict) -> int:
    """D-DD.129: v8 with exactly one generator and one inverter (Kobo), else v9."""
    kinds = [c["type"] for c in site["foundation"]["components"]]
    return 8 if all(kinds.count(kind) == 1 for kind in UNIT_KINDS) else 9


def _book(books: dict, key: str, code: str):
    """A required book key (D-DD.129: no hidden default)."""
    if key not in books:
        raise TelemetryRefused("TEL_BOOKS", f"{code} the books carry no {key}")
    return books[key]


def _property(component: dict, key: str, code: str) -> Fraction:
    for item in component["properties"]:
        if item["property_key"] == key:
            return Fraction(item["value"])
    raise TelemetryRefused("TEL_FOUNDATION", f"{code} {key}")


def _month_days(month: str) -> list[date]:
    year, number = parse_month(month)
    day = date(year, number, 1)
    days = []
    while day.month == number:
        days.append(day)
        day += timedelta(days=1)
    return days


def _load_blocks(month: str, weights: dict, books: dict, code: str) -> dict[tuple[date, str, int], Fraction]:
    """Largest remainder over the month's (day, feeder, hour) blocks: Wh per block, summing to `delivered_kwh` x 1000.
    The month's weights are those of the whole month whatever span is run, so a day's values never depend on the span.
    A month with no books (`rate_of`, D-DD.103) has the blocks of its days and hours inside `READINGS_SPAN`."""
    book = books["months"][month]
    delivered = book["delivered_kwh"]
    keys, shares = [], []
    classes = weights["classes"]
    for day in _month_days(month):
        weight = Fraction(weights[day_class(day, classes)])
        hours = _span_hours(day) if "rate_of" in book else range(24)
        for feeder in sorted(LOAD_SHAPE_KW):
            for hour in hours:
                keys.append((day, feeder, hour))
                shares.append(weight * LOAD_SHAPE_KW[feeder][hour])
    if sum(shares, Fraction(0)) == 0:
        raise TelemetryRefused("TEL_INPUT_TOTAL", f"{code} {month} the load shape has no energy")
    if delivered <= 0:
        raise TelemetryRefused("TEL_INPUT_TOTAL", f"{code} {month} delivered_kwh {delivered} cannot be met")
    wh = allocate(delivered * 1000, shares)
    if sum(wh) != delivered * 1000:
        raise TelemetryRefused("TEL_INPUT_TOTAL", f"{code} {month} delivered_kwh {delivered}")
    return {key: Fraction(value) for key, value in zip(keys, wh)}


def _draws(month: str, books: dict) -> dict[date, Fraction]:
    """The month's `unexplained_l`, in equal daily parts to 0.01 L, largest remainder to the earlier days."""
    days = _month_days(month)
    centilitres = allocate(int(books["months"][month]["unexplained_l"]) * 100, [Fraction(1)] * len(days))
    return {day: Fraction(c, 100) for day, c in zip(days, centilitres)}


def _draw(day: date, books: dict, code: str) -> Fraction:
    """The day's declared draw. A month with no books draws its rate month's part of the same day of month (D-DD.103)."""
    book = books["months"][day.strftime("%Y-%m")]
    if "rate_of" not in book:
        return _draws(day.strftime("%Y-%m"), books)[day]
    parts = _draws(book["rate_of"], books)
    year, number = parse_month(book["rate_of"])
    try:
        return parts[date(year, number, day.day)]
    except (KeyError, ValueError):
        raise TelemetryRefused("TEL_INPUT_TOTAL", f"{code} {day.isoformat()} has no day {day.day} in "
                                                  f"{book['rate_of']}") from None


def _sun(day: date, weights: dict, code: str) -> tuple[Fraction, ...]:
    """Season v2's day on its calendar at its Sites; any other day the clear shape times the `solar_surplus` weight
    (D-DD.77, D-DD.129)."""
    if code in SEASON_V2_SUN_SITES and SEASON_V2_DAY_ZERO <= day <= SEASON_V2_LAST_DAY:
        kind = "overcast" if (day - SEASON_V2_DAY_ZERO).days in OVERCAST_DAYS else "clear"
        return tuple(Fraction(v) for v in SUN_W_PER_M2[kind])
    season = weights["seasons"].get(day.strftime("%Y-%m"))
    if season is None:
        raise TelemetryRefused("TEL_FOUNDATION", f"{code} {day.isoformat()} has no declared season for the sun")
    weight = Fraction(weights["season"][season]) * Fraction(weights["day"][day_class(day, weights["classes"])])
    return tuple(Fraction(v) * weight for v in SUN_W_PER_M2["clear"])


def _unit_events(site: dict, zone: ZoneInfo, start: datetime, end: datetime) -> list[ForcingInput]:
    """The Site's `UNIT_EVENTS` inside the span, each a one-minute WINDOW at its instant (D-DD.145)."""
    units = {c["id"] for c in site["foundation"]["components"] if c["type"] in UNIT_KINDS}
    out = []
    for event in UNIT_EVENTS:
        if event["site"] != site["code"]:
            continue
        if event["unit"] not in units:
            raise TelemetryRefused("TEL_FOUNDATION", f"{site['code']} {event['source']} names no unit {event['unit']}")
        at = datetime.fromisoformat(event["at"]).astimezone(timezone.utc)
        if not start <= at < end:
            continue
        offset = int((at - start).total_seconds() // 60)
        out.append(ForcingInput(
            event_id=f"{event['kind']}:{event['unit']}:{event['at']}", address=f"{event['kind']}@{event['unit']}",
            state_key=event["kind"], parameter_id="unit-event", value=Fraction(1), canonical_unit="1", dimension="COUNT",
            shape="WINDOW", offset_minutes=offset, duration_minutes=1, requirement="REQUIRED"))
    return out


def frozen_inputs(site: dict, books: dict, first: str, last: str) -> FrozenWorldInputs:
    """The Site's one frozen input record for the span (D-DD.69), from `F` and the books alone. Its starting state of
    charge is the midnight state after one warm-up day (D-DD.104, `warm_up_soc`)."""
    return _frozen(site, books, first, last, start_soc=warm_up_soc(site, books, first))


def warm_up_soc(site: dict, books: dict, first: str) -> Fraction:
    """D-DD.104: one day of the span's first day's load and sun (no fuel note, no draw, no unit event), from the lead
    generator's declared stop threshold, with the tank as declared; the state of charge at its end, exact."""
    code, foundation = site["code"], site["foundation"]
    threshold = _property(_component(foundation, "GENERATOR", code), "stop-soc-threshold", code)
    day = first[:10]
    frozen = _frozen(site, books, day, day, start_soc=threshold, warm_up=True)
    execution = start_execution(frozen, MODELS[frozen.model_profile_version])
    execution.run_to_end()
    if execution.outcome != "COMPLETED":
        raise TelemetryRefused("TEL_PACK", f"{code} the warm-up day {day} {execution.failure}")
    battery = _component(foundation, "BATTERY", code)["id"]
    soc = execution.boundaries[-1].state_sample(f"{SOC_ADDRESS}@{battery}")
    if soc is None:
        raise TelemetryRefused("TEL_PACK", f"{code} the warm-up day {day} ends with no state of charge")
    return soc


def _frozen(site: dict, books: dict, first: str, last: str, *, start_soc: Fraction,
            warm_up: bool = False) -> FrozenWorldInputs:
    code, foundation, zone = site["code"], site["foundation"], _zone(site)
    version = pack_version(site)
    model = MODELS[version]
    days, end_minute = span_days(first, last)
    start, end = _utc(zone, days[0]), _utc(zone, days[-1], end_minute)
    duration = (len(days) - 1) * 1440 + end_minute
    if (end - start) != timedelta(minutes=duration):
        raise TelemetryRefused("TEL_FOUNDATION", f"{code} a clock change inside {first}..{last}")
    ids = {kind: _component(foundation, kind, code)["id"] for kind in
           ("PV_ARRAY", "INVERTER", "BATTERY", "POWER_CONVERSION_SYSTEM", "GENERATOR", "FUEL_TANK", "AC_BUS")}
    generators = [c["id"] for c in _units(foundation, "GENERATOR", code)]
    inverters = [c["id"] for c in _units(foundation, "INVERTER", code)]
    loads = [c["id"] for c in foundation["components"] if c["type"] == "LOAD"]

    initial = []
    for need in NEEDS:
        if need.version is not None and need.version != version:
            continue
        if need.component_type in UNIT_KINDS and need.per_unit:
            components = _units(foundation, need.component_type, code)
        else:
            components = [_component(foundation, need.component_type, code)]
        for component in components:
            value = _property(component, need.property_key, code) / need.divisor
            initial.append(InitialValue(address=f"{need.state_key}@{component['id']}", state_key=need.state_key,
                                        scope="COMPONENT", parameter_id=f"model-need:{need.property_key}", value=value,
                                        canonical_unit=need.unit, dimension=need.dimension,
                                        answered_by="SITE_FOUNDATION"))
    capacity = next(row.value for row in initial if row.state_key == "fuel-tank-capacity")
    tank = f"{TANK_ADDRESS}@{ids['FUEL_TANK']}"
    initial += [
        InitialValue(address=f"{SOC_ADDRESS}@{ids['BATTERY']}", state_key=SOC_ADDRESS, scope="COMPONENT",
                     parameter_id="starting-state-of-charge", value=start_soc,
                     canonical_unit="%", dimension="FRACTION", answered_by="SCENARIO"),
        InitialValue(address=tank, state_key=TANK_ADDRESS, scope="COMPONENT", parameter_id="starting-fuel",
                     value=capacity * TANK_START_FRACTION, canonical_unit="L", dimension="VOLUME",
                     answered_by="SCENARIO")]
    bounds = (DeclaredBound(address=tank, kind="UPPER", value=capacity, canonical_unit="L",
                            source_address=f"fuel-tank-capacity@{ids['FUEL_TANK']}", bound_case_id="fuel-tank-capacity",
                            policy="BOUNDED_AND_RECORDED"),)

    forcings = []
    months = sorted({day.strftime("%Y-%m") for day in days})
    for month in months:
        if month not in books["months"]:
            raise TelemetryRefused("TEL_INPUT_TOTAL", f"{code} {month} has no books")
    blocks = {month: _load_blocks(month, books["day_weights"], books, code) for month in months}
    load_ids = {_feeder(load): load for load in loads}
    sun_weights = _book(books, "sun_weights", code)
    notes = _book(books, "fuel_notes", code)
    for index, day in enumerate(days):
        base = index * 1440
        month_blocks = blocks[day.strftime("%Y-%m")]
        sun = _sun(day, sun_weights, code)
        for hour in range(end_minute // 60 if day == days[-1] else 24):
            offset = base + hour * 60
            forcings.append(ForcingInput(
                event_id=f"sun:{offset}", address=IRRADIANCE, state_key="plane-of-array-irradiance",
                parameter_id="world-sun", value=sun[hour], canonical_unit="W/m2", dimension="IRRADIANCE",
                shape="WINDOW", offset_minutes=offset, duration_minutes=60, requirement="REQUIRED"))
            for feeder in sorted(load_ids):
                kw = month_blocks[(day, feeder, hour)] / 1000  # Wh over one hour is Wh / 1000 kW
                forcings.append(ForcingInput(
                    event_id=f"load:{feeder}:{offset}", address=f"load-demand@{load_ids[feeder]}",
                    state_key="load-demand", parameter_id="world-load", value=kw, canonical_unit="kW",
                    dimension="POWER", shape="WINDOW", offset_minutes=offset, duration_minutes=60, requirement="REQUIRED"))
    if not warm_up:
        forcings += _unit_events(site, zone, start, end)

    causes = []
    for note in () if warm_up else notes:
        at = datetime.fromisoformat(note["at"]).astimezone(zone)
        local_day = at.date()
        if local_day < days[0] or local_day > days[-1] or at.astimezone(timezone.utc) >= end:
            continue
        offset = int((at.astimezone(timezone.utc) - start).total_seconds() // 60)
        if (at.astimezone(timezone.utc) - start).total_seconds() % (STEP_MINUTES * 60):
            raise TelemetryRefused("TEL_EVENT_UNPLACED", f"{code} {note['at']} is not on a {STEP_MINUTES}-minute step")
        causes.append(DeclaredCause(
            event_id=f"delivery:{note['at']}", address=tank, state_key=TANK_ADDRESS, direction="INCREASE",
            parameter_id="fuel-note", quantity=Fraction(note["litres"]), canonical_unit="L", dimension="VOLUME",
            shape="POINT", offset_minutes=offset, duration_minutes=None))
    for index, day in enumerate(() if warm_up else days):
        if day == days[-1] and DRAW_MINUTE >= end_minute:
            continue
        draw = _draw(day, books, code)
        if draw:
            causes.append(DeclaredCause(
                event_id=f"draw:{day.isoformat()}", address=tank, state_key=TANK_ADDRESS, direction="DECREASE",
                parameter_id="declared-draw", quantity=draw, canonical_unit="L", dimension="VOLUME", shape="POINT",
                offset_minutes=index * 1440 + DRAW_MINUTE, duration_minutes=None))
    causes.sort(key=lambda c: (c.offset_minutes, c.event_id))

    pcs, battery, generator, pv = ids["POWER_CONVERSION_SYSTEM"], ids["BATTERY"], ids["GENERATOR"], ids["PV_ARRAY"]
    ordered = sorted(loads, key=lambda load: (CRITICAL_ORDER.index(_feeder(load)), load))
    digest = site["foundation_digest"]
    discrete = tuple(DiscreteInitialValue(address=f"{STATE_ADDRESS}@{unit}", state_key=STATE_ADDRESS, scope="COMPONENT",
                                          value="STOPPED", answered_by="SCENARIO") for unit in generators)
    if version == 9:
        discrete += tuple(DiscreteInitialValue(address=f"inverter-state@{unit}", state_key="inverter-state",
                                               scope="COMPONENT", value="AVAILABLE", answered_by="SCENARIO")
                          for unit in inverters)
    return FrozenWorldInputs(
        run_id=f"world-{code}", execution_contract_version=EXECUTION_CONTRACT_VERSION, site_id=code,
        foundation_version=1, scenario_id="world-telemetry", scenario_version=1,
        model_profile_id=model.model_profile_id, model_profile_version=model.model_profile_version,
        publication_profile_id="simulator-lab-publication", publication_profile_version=3,
        interval=FrozenInterval(start_time=_iso_utc(start), end_time=_iso_utc(end), duration_minutes=duration,
                                timestep_minutes=STEP_MINUTES),
        seed=int(digest[:8], 16), initial_values=tuple(initial), bounds=bounds, forcings=tuple(forcings),
        causes=tuple(causes), unmodelled_inputs=(), reporting_path_addresses=(), intervention_history=(),
        site_controls=(SiteControlInput("source-priority", (pv, battery, generator)),
                       SiteControlInput("critical-load-priority", tuple(ordered))),
        bus_attachments=(
            *(BusAttachmentInput("PV_SOURCE", pv, inverter, ids["AC_BUS"]) for inverter in inverters),
            BusAttachmentInput("STORAGE", battery, pcs, ids["AC_BUS"]),
            *(attachment for unit in generators for attachment in (
                BusAttachmentInput("GENERATION", unit, None, ids["AC_BUS"]),
                BusAttachmentInput("FUEL_SUPPLY", ids["FUEL_TANK"], unit, ids["AC_BUS"]))),
            *(BusAttachmentInput("LOAD", load, None, ids["AC_BUS"]) for load in ordered)),
        discrete_initial_values=discrete)


# --- public records to readings ----------------------------------------------------------------------------------------

#: (role) -> (state key, component type, reading class). The pack's public record for each role (publication profile
#: `simulator-lab-publication` v3 and v3's measures); `irradiance` has no pack record: it is the sun the run was given.
PUBLIC_RECORDS: dict[str, tuple[str, str, str]] = {
    "pv_power": ("pv-ac-power", "INVERTER", "INTERVAL"),
    "pv_available_power": ("pv-available-power", "INVERTER", "INTERVAL"),
    "pv_irradiance": (IRRADIANCE, "PV_ARRAY", "SUN"),
    "battery_power": ("battery-ac-power", "POWER_CONVERSION_SYSTEM", "INTERVAL"),
    "battery_soc": (SOC_ADDRESS, "BATTERY", "STATE"),
    "pcs_discharge_capability": ("battery-discharge-capability", "POWER_CONVERSION_SYSTEM", "INTERVAL"),
    "generator_power": ("generator-output-power", "GENERATOR", "INTERVAL"),
    "generator_state": (STATE_ADDRESS, "GENERATOR", "DISCRETE"),
    "fuel_level": (TANK_ADDRESS, "FUEL_TANK", "STATE"),
    "feeder_demand": ("load-served-power", "LOAD", "INTERVAL"),
}


def readings_bytes(rows: list[dict]) -> bytes:
    """One canonical JSON line per reading, in the order given."""
    return ("\n".join(canonical_bytes(row).decode("utf-8") for row in rows) + "\n").encode("utf-8")


def _decimal(value: Fraction) -> str:
    return str(Decimal(value.numerator).__truediv__(Decimal(value.denominator)).quantize(QUANTUM, rounding=ROUND_HALF_EVEN))


class SiteRun:
    """One Site's continuous execution over the span, read a day (or any run of steps) at a time."""

    def __init__(self, site: dict, books: dict, first: str, last: str) -> None:
        self.site, self.books = site, books
        self.code, self.zone = site["code"], _zone(site)
        self.days, self.end_minute = span_days(first, last)
        self.day_steps = [STEPS_PER_DAY] * (len(self.days) - 1) + [self.end_minute // STEP_MINUTES]
        self.frozen = frozen_inputs(site, books, first, last)
        self.pack = ("mini-grid", self.frozen.model_profile_version)
        self.start_soc = next(r.value for r in self.frozen.initial_values if r.state_key == SOC_ADDRESS)
        self.pairs, self.mappings = self._resolve()
        self._execution = start_execution(self.frozen, MODELS[self.frozen.model_profile_version])
        self.steps_advanced = 0
        self._started = False
        self._bounded_seen = 0
        self.refused_litres = Fraction(0)
        self.strict = True  # False: a bounded transition is recorded, not refused (the pure run's table only)
        self.next_day = 0
        self.ledger: dict[str, dict] = {}
        self._day_rows: dict[date, list[dict]] = {}
        values = {row.address: row.value for row in self.frozen.initial_values}
        #: each generator unit's own fuel curve (D-DD.129: the ledger burns each unit on its curve and sums)
        self._curves = {
            unit["id"]: generator_curve.fuel_curve(values[f"generator-specific-fuel-consumption@{unit['id']}"],
                                                   values[f"generator-no-load-fuel-rate@{unit['id']}"],
                                                   values[f"generator-rated-power@{unit['id']}"])
            for unit in _units(site["foundation"], "GENERATOR", self.code)}
        self._tank = next(r.address for r in self.frozen.initial_values if r.state_key == TANK_ADDRESS)
        #: D-DD.145/146: a generator unit's state row of the step holding its event starts at the event's instant
        self._stamps = {}
        for forcing in self.frozen.forcings:
            if forcing.state_key in ("unit-fail", "unit-restore"):
                unit = forcing.address.split("@", 1)[1]
                at = (self._start_utc() + timedelta(minutes=forcing.offset_minutes)).astimezone(self.zone)
                self._stamps[(f"{STATE_ADDRESS}@{unit}", forcing.offset_minutes // STEP_MINUTES + 1)] = at
        self._pcs = next(r.address for r in self.frozen.initial_values
                         if r.state_key == "pcs-charge-limit").split("@")[1]
        self._start = self._start_utc()

    def _start_utc(self) -> datetime:
        return datetime.fromisoformat(self.frozen.interval.start_time.replace("Z", "+00:00"))

    # -- the binding of every public record (D-DD.72) --

    def _resolve(self) -> tuple[list[dict], list[dict]]:
        foundation, code = self.site["foundation"], self.code
        pairs, mappings = [], []
        for role in sorted(PUBLIC_RECORDS):
            state_key, component_type, kind = PUBLIC_RECORDS[role]
            rows = [b for b in self.site["bindings"] if b["role"] == role]
            for row in rows:
                component = next((c for c in foundation["components"] if c["id"] == row["asset_code"]), None)
                if component is None or component["type"] != component_type:
                    raise TelemetryRefused("TEL_BINDING", f"{code} {role}")
            if role == "feeder_demand" or component_type in UNIT_KINDS:
                # PER_ASSET roles (D-DD.129): one row for each load or unit, each its own component
                targets = [(row, row["asset_code"]) for row in rows]
                expected = {c["id"] for c in foundation["components"] if c["type"] == component_type}
                if len(targets) != len(expected) or {t[1] for t in targets} != expected:
                    raise TelemetryRefused("TEL_BINDING", f"{code} {role}")
            else:
                if len(rows) != 1:
                    raise TelemetryRefused("TEL_BINDING", f"{code} {role}")
                targets = [(rows[0], rows[0]["asset_code"])]
            for row, component_id in targets:
                address = state_key if kind == "SUN" else f"{state_key}@{component_id}"
                pairs.append({"role": role, "kind": kind, "address": address, "source_id": row["device_id"],
                              "signal_id": row["signal_id"], "unit": row["source_unit"], "conversion": row["conversion"]})
                mappings.append({"record": address, "role": role, "source_id": row["device_id"],
                                 "signal_id": row["signal_id"]})
        seen = {(p["source_id"], p["signal_id"]) for p in pairs}
        if len(seen) != len(pairs):
            raise TelemetryRefused("TEL_BINDING", f"{code} a device signal is bound to two roles")
        pairs.sort(key=lambda p: (p["source_id"], p["signal_id"]))
        return pairs, sorted(mappings, key=lambda m: (m["source_id"], m["signal_id"]))

    # -- advancing --

    def _pack_refusal(self, step_from: int) -> TelemetryRefused | None:
        execution = self._execution
        failure = execution.failure
        day = self._day_text(step_from)
        if failure is not None:
            return TelemetryRefused("TEL_PACK", f"{self.code} {day} {failure.kind} {failure.subject}")
        bounded = execution.bounded_transitions
        if len(bounded) > self._bounded_seen:
            new = bounded[self._bounded_seen:]
            self._bounded_seen = len(bounded)
            self.refused_litres += sum((t.refused for t in new), Fraction(0))
            first = new[0]
            return TelemetryRefused("TEL_PACK", f"{self.code} {day} {first.bound_case_id} refused {_decimal(first.refused)} L "
                                                f"at {first.address}")
        return None

    def _day_text(self, step: int) -> str:
        return self.days[min(max(step - 1, 0) // STEPS_PER_DAY, len(self.days) - 1)].isoformat()

    def advance(self, steps: int, *, strict: bool = True) -> None:
        if not self._started:
            self._execution.advance(1)  # the first boundary: the declared initial state
            self._started = True
        before = self.steps_advanced
        done = self._execution.advance(steps)
        self.steps_advanced += done
        refusal = self._pack_refusal(before + 1)
        if refusal is not None and (strict and self.strict or self._execution.failure is not None):
            raise refusal
        if done < steps and strict:
            raise TelemetryRefused("TEL_PACK", f"{self.code} {self._day_text(before + done)} the execution stopped early")

    def readings_for_steps(self, first_step: int, last_step: int) -> list[dict]:
        """Advance to `last_step` (steps from the span's start, 1-based) and read steps `first_step..last_step`."""
        if last_step > self.steps_advanced:
            self.advance(last_step - self.steps_advanced)
        boundaries = self._execution.boundaries
        out = []
        for step in range(first_step, last_step + 1):
            boundary, start_minute = boundaries[step], (step - 1) * STEP_MINUTES
            end_at = (self._start + timedelta(minutes=step * STEP_MINUTES)).astimezone(self.zone)
            start_at = (self._start + timedelta(minutes=start_minute)).astimezone(self.zone)
            self._account(start_at, boundaries[step - 1], boundary, step)
            for pair in self.pairs:
                value = self._value(pair, boundary, boundaries[step - 1])
                stamp = self._stamps.get((pair["address"], step), start_at) if pair["kind"] == "DISCRETE" else start_at
                out.append({"source_id": pair["source_id"], "signal_id": pair["signal_id"],
                            "start": stamp.isoformat(), "end": end_at.isoformat(), "value": value, "unit": pair["unit"]})
        return sorted(out, key=lambda r: (r["start"], r["source_id"], r["signal_id"]))

    def _account(self, start_at: datetime, previous, boundary, step: int) -> None:
        """The month ledger: what the measured books and the pure-run table are written from (not published)."""
        month = start_at.strftime("%Y-%m")
        tank = boundary.stock(self._tank)
        row = self.ledger.get(month)
        if row is None:
            opening = previous.stock(self._tank)
            row = self.ledger[month] = {
                "demand_kwh": {}, "served_kwh": {}, "unserved_kwh": {}, "generator_kwh": Fraction(0),
                "generator_minutes": 0, "tank_open": opening, "tank_min": opening, "tank_max": opening,
                "modelled_l": Fraction(0), "standin_candidate_l": Fraction(0), "starts": 0, "steps": 0}
        row["steps"] += 1
        row["tank_close"], row["tank_min"], row["tank_max"] = tank, min(row["tank_min"], tank), max(row["tank_max"], tank)
        step = previous.control_step
        for load in step.accepted.loads if step is not None else ():
            feeder = load.address.split("@")[-1]
            for key, value in (("demand_kwh", load.demand_energy), ("served_kwh", load.served_energy),
                               ("unserved_kwh", load.unserved_energy)):
                row[key][feeder] = row[key].get(feeder, Fraction(0)) + value
        energy, litres = Fraction(0), Fraction(0)
        for unit, curve in self._curves.items():
            unit_energy = boundary.interval_measurement(f"generator-output-power@{unit}")
            state = previous.discrete_state_for_step(f"{STATE_ADDRESS}@{unit}")
            if unit_energy is None or state is None:
                raise TelemetryRefused("TEL_PACK", f"{self.code} {unit} step {step} ({start_at.isoformat()}) has no "
                                                   f"{'output' if unit_energy is None else 'state'}")
            energy += unit_energy
            litres += generator_curve.fuel_litres(curve, state, Fraction(STEP_MINUTES), unit_energy)
            if state == "RUNNING":
                row["generator_minutes"] += STEP_MINUTES  # unit-minutes: each running unit counts
        row["generator_kwh"] += energy
        row["modelled_l"] += litres
        if energy > 0:
            capability = boundary.interval_measurement(f"battery-discharge-capability@{self._pcs}")
            if capability is not None and capability >= energy:
                row["standin_candidate_l"] += litres  # a stand-in: the battery could have carried this slot

    def next_day_readings(self) -> list[dict]:
        index = self.next_day
        if index >= len(self.days):
            raise IndexError("the span is complete")
        self.next_day += 1
        first = index * STEPS_PER_DAY + 1
        return self.readings_for_steps(first, first + self.day_steps[index] - 1)

    def measured_months(self) -> dict[str, dict]:
        """D-DD.99 mini-grid `<month>` (DD3a's, unchanged), exact; the frame rounds once."""
        return {month: {"demand_kwh": dict(row["demand_kwh"]), "served_kwh": dict(row["served_kwh"]),
                        "unserved_kwh": dict(row["unserved_kwh"]), "generator_kwh": row["generator_kwh"]}
                for month, row in sorted(self.ledger.items())}

    def advance_day(self) -> date:
        """D-DD.81's day-level protocol: step the next local day and keep its rows (already bound by this frame)."""
        day = self.days[self.next_day]
        self._day_rows[day] = self.next_day_readings()
        return day

    def day_records(self, day: date) -> list[dict]:
        return self._day_rows.pop(day)

    @property
    def end_local(self) -> datetime:
        """The span's end instant, local time (D-DD.103)."""
        return datetime.fromisoformat(self.frozen.interval.end_time.replace("Z", "+00:00")).astimezone(self.zone)

    def _value(self, pair: dict, boundary, previous) -> str:
        kind, address = pair["kind"], pair["address"]
        if kind == "SUN":
            exposure = previous.forcing(address)
            return _decimal(Fraction(0) if exposure is None else exposure)
        if kind == "DISCRETE":
            member = boundary.discrete_state(address)
            allowed = pair["conversion"].get("parameters", {}).get("map", {})
            if member is None or member not in allowed:  # an empty map admits nothing (D-DD.129)
                raise TelemetryRefused("TEL_BINDING", f"{self.code} {pair['role']} state {member}")
            return member
        if kind == "STATE":
            sample = boundary.state_sample(address)
        else:
            measured = boundary.interval_measurement(address)
            sample = None if measured is None else measured / HOURS_PER_STEP
        if sample is None:
            raise TelemetryRefused("TEL_PACK", f"{self.code} {boundary.simulation_time} {address} has no value")
        return _decimal(sample)


@dataclass(frozen=True)
class TelemetryResult:
    files: tuple[tuple[str, bytes], ...]
    manifests: tuple[tuple[str, dict], ...]


def day_file(site: dict, day: date, rows: list[dict]) -> bytes:
    head = canonical_bytes({"day": day.isoformat(), "role_set": site["role_set"], "schema": READINGS_SCHEMA,
                            "site_code": site["code"], "timezone": site["timezone"]}).decode("utf-8")
    body = ",\n".join(canonical_bytes(row).decode("utf-8") for row in rows)
    return (head[:-1] + ',"readings":[\n' + body + "\n]}\n").encode("utf-8")


#: D-DD.81: a Site's pack family, by its binding role set's family (the role set's name before its version).
PACK_FAMILIES = {"minigrid-roles": "mini-grid", "cold-roles": "cold-thermal", "ev-roles": "ev-charger"}
#: The vertical pack each family's run drives (model, version), written in its readings manifest.
VERTICAL_PACKS = {"cold-thermal": ("cold-thermal", 2), "ev-charger": ("ev-charger", 1)}


def pack_family(site: dict) -> str | None:
    return PACK_FAMILIES.get(site["role_set"].rsplit("-", 1)[0])


class VerticalBinding:
    """The frame's binding of a vertical run's pack rows (D-DD.81, D-DD.91): each `(device_id, signal_id)` resolves to
    exactly one binding row; a value is rounded to the millesimal or checked against the binding's state map; an event
    row has value null, unit `event` and its `event` object. Rows sort by (start, source_id, signal_id, ordinal)."""

    def __init__(self, site: dict) -> None:
        self.code, self.zone = site["code"], _zone(site)
        self.rows_by_channel: dict[tuple[str, str], dict] = {}
        for row in site["bindings"]:
            key = (row["device_id"], row["signal_id"])
            if key in self.rows_by_channel:
                raise TelemetryRefused("TEL_BINDING", f"{self.code} {key[0]}/{key[1]} has two binding rows")
            self.rows_by_channel[key] = row
        # D-DD.123: a run that names a channel by its bound asset (EV: `ch-k1-c1`, `site-meter`) resolves through the
        # binding's `asset_code` when no binding row's `device_id` carries that name; an asset bound twice refuses.
        self.by_asset: dict[tuple[str, str], dict | None] = {}
        for row in site["bindings"]:
            key = (row["asset_code"], row["signal_id"])
            self.by_asset[key] = None if key in self.by_asset else row
        self.used: set[tuple[str, str]] = set()

    def rows(self, pack_rows: list[tuple]) -> list[dict]:
        out = []
        for device, signal, start, end, value, unit, event in pack_rows:
            binding = self.rows_by_channel.get((device, signal)) or self.by_asset.get((device, signal))
            if binding is None:
                bound_twice = (device, signal) in self.by_asset
                raise TelemetryRefused("TEL_BINDING", f"{self.code} {device}/{signal} is bound twice by asset_code" if bound_twice
                                       else f"{self.code} {device}/{signal} has no binding row")
            self.used.add((binding["device_id"], binding["signal_id"]))
            row = {"source_id": binding["device_id"], "signal_id": binding["signal_id"],
                   "start": start.astimezone(self.zone).isoformat(), "end": end.astimezone(self.zone).isoformat()}
            if event is not None:
                if binding["source_unit"] != "event":
                    raise TelemetryRefused("TEL_BINDING", f"{self.code} {device}/{signal} is an event channel bound "
                                                          f"as {binding['source_unit']}")
                row.update(value=None, unit="event", event=dict(event))
            else:
                if unit != binding["source_unit"]:
                    raise TelemetryRefused("TEL_BINDING", f"{self.code} {device}/{signal} {unit} bound as "
                                                          f"{binding['source_unit']}")
                if isinstance(value, Fraction):
                    text = _decimal(value)
                elif isinstance(value, str):
                    allowed = binding["conversion"].get("parameters", {}).get("map", {})
                    if value not in allowed:  # an empty map admits nothing (D-DD.129)
                        raise TelemetryRefused("TEL_BINDING", f"{self.code} {device}/{signal} state {value}")
                    text = value
                else:
                    raise TelemetryRefused("TEL_PACK", f"{self.code} {start.isoformat()} {device}/{signal} has no value")
                row.update(value=text, unit=binding["source_unit"])
            out.append(row)
        return sorted(out, key=lambda r: (r["start"], r["source_id"], r["signal_id"],
                                          r["event"]["ordinal"] if "event" in r else 0))

    def mappings(self) -> list[dict]:
        return [{"record": self.rows_by_channel[k]["asset_code"], "role": self.rows_by_channel[k]["role"],
                 "source_id": k[0], "signal_id": k[1]} for k in sorted(self.used)]


def supported(site: dict) -> bool:
    """D-DD.129: one BATTERY and one FUEL_TANK, at least one GENERATOR and one INVERTER."""
    kinds = [c["type"] for c in site["foundation"]["components"]]
    return (all(kinds.count(kind) == 1 for kind in ("BATTERY", "FUEL_TANK"))
            and all(kinds.count(kind) >= 1 for kind in UNIT_KINDS))


def build_telemetry(view: dict, sites: dict, decided_books: dict, *, start: str, end: str,
                    only: tuple[str, ...] | None = None, sink=None) -> TelemetryResult:
    """`view` the allowlisted manifest view, `sites` the `F` file, `decided_books` per Site code (see `books_for`).
    `start` is the first local day; `end` the last local day (whole) or a local end instant (D-DD.103).
    `sink(name, data)`, when given, receives each file as it is made and the result holds none (DD4b run 5: the CLI
    writes and drops each day file); without it the files are collected and returned, in the same order."""
    refuse_oracle(sites)
    files, manifests = [], []
    emit = sink if sink is not None else (lambda name, data: files.append((name, data)))
    by_tenant: dict[str, list[SiteRun]] = {}
    for site in sites.get("unbound", []):  # D-DD.129: a Site with no binding conversion is stated, not skipped
        if only is None or site["code"] in only:
            manifests.append((f"{site['tenant']}/telemetry/{site['code']}.manifest.json", {
                "schema": MANIFEST_SCHEMA, "site_code": site["code"],
                "not_written": "TEL_BINDING the Site has no binding conversion"}))
    for site in sites["sites"]:
        code = site["code"]
        if only is not None and code not in only:
            continue
        family = pack_family(site)
        if family in VERTICAL_PACKS:
            vertical_run = _vertical(site, family, decided_books[code], start, end, manifests, emit)
            by_tenant.setdefault(site["tenant"], []).append(vertical_run)
            continue
        if family != "mini-grid" or not supported(site):
            manifests.append((f"{site['tenant']}/telemetry/{code}.manifest.json", {"schema": MANIFEST_SCHEMA, "site_code": code,
                                                        "not_written": "TEL_PACK no pack for this structure yet (DD3.3)"}))
            continue
        run = SiteRun(site, decided_books[code], start, end)
        digests: dict[str, "hashlib._Hash"] = {}
        for day in run.days:
            data = day_file(site, run.advance_day(), run.day_records(day))
            emit(f"{site['tenant']}/telemetry/{code}.{day.isoformat()}.readings.json", data)
            digests.setdefault(day.strftime("%Y-%m"), hashlib.sha256()).update(data)
        by_tenant.setdefault(site["tenant"], []).append(run)
        manifests.append((f"{site['tenant']}/telemetry/{code}.manifest.json", site_manifest(
            site, run, decided_books[code], {m: d.hexdigest() for m, d in sorted(digests.items())})))
    for slug, runs in sorted(by_tenant.items()):
        emit(f"{slug}/telemetry/measured.json", file_bytes(measured_for(slug, runs)))
    return TelemetryResult(tuple(files), tuple(manifests))


def _vertical(site: dict, family: str, books: dict, start: str, end: str, manifests: list, emit) -> object:
    """A vertical Site's run (D-DD.81): its pack rows bound, rounded and written by this frame, a day at a time. Each
    day file goes to `emit` and the run's rows of that day are released once written (DD4b run 5)."""
    run = _vertical_runs()[family](site, books, start, end)
    binding = VerticalBinding(site)
    digests = {}
    for day in run.days:
        run.advance_day()
        data = day_file(site, day, binding.rows(run.day_records(day)))
        run.release_day(day)
        emit(f"{site['tenant']}/telemetry/{site['code']}.{day.isoformat()}.readings.json", data)
        digests.setdefault(day.strftime("%Y-%m"), hashlib.sha256()).update(data)
    model, version = VERTICAL_PACKS[family]
    manifests.append((f"{site['tenant']}/telemetry/{site['code']}.manifest.json", {
        "schema": MANIFEST_SCHEMA, "generator": GENERATOR, "site_code": site["code"], "role_set": site["role_set"],
        "pack": {"model": model, "version": version}, "foundation_digest": site["foundation_digest"],
        "span": {"first": run.days[0].isoformat(), "last": run.days[-1].isoformat(),
                 "to": run.end.astimezone(_zone(site)).isoformat()},
        "private_parameters": run.private_parameters(), "conditions": run.conditions(),
        "mappings": binding.mappings(), "golden_digests": {m: d.hexdigest() for m, d in sorted(digests.items())}}))
    return _measured_view(run)


def _measured_view(run) -> object:
    """What `measured_for` reads of a finished vertical run, taken now so the run's day rows are not held."""
    from types import SimpleNamespace

    months = run.measured_months()
    view = SimpleNamespace(code=run.code, days=[run.days[-1]], end_local=run.end_local, zone=run.zone,
                           measured_months=lambda: months)
    if hasattr(run, "departures"):
        departed = run.departures()
        view.departures = lambda: departed
    return view


def site_manifest(site: dict, run: SiteRun, books: dict, golden: dict[str, str]) -> dict:
    return {
        "schema": MANIFEST_SCHEMA, "generator": GENERATOR, "site_code": site["code"], "role_set": site["role_set"],
        "pack": {"model": run.pack[0], "version": run.pack[1]}, "foundation_digest": site["foundation_digest"],
        "span": {"first": run.days[0].isoformat(), "last": run.days[-1].isoformat(), "to": run.end_local.isoformat()},
        "private_parameters": {a.address: str(a.value) for a in run.frozen.initial_values},
        "conditions": {
            "load_shape_kw": {k: list(v) for k, v in sorted(LOAD_SHAPE_KW.items())},
            "load_shape_basis": LOAD_SHAPE_BASIS,
            "start_soc": {"value": _decimal(run.start_soc), "unit": "%", "basis": START_SOC_BASIS},
            "unit_events": [dict(e) for e in UNIT_EVENTS if e["site"] == site["code"]],
            "unit_event_timing": UNIT_EVENT_TIMING,
            "sun_w_per_m2": {k: list(v) for k, v in sorted(SUN_W_PER_M2.items())},
            "overcast_days_from": SEASON_V2_DAY_ZERO.isoformat(), "overcast_day_indices": sorted(OVERCAST_DAYS),
            "sun_outside_calendar": {"rule": SUN_RULE, "calendar": [SEASON_V2_DAY_ZERO.isoformat(),
                                                                     SEASON_V2_LAST_DAY.isoformat()],
                                     "sites": list(SEASON_V2_SUN_SITES), "weights": books["sun_weights"]},
            "day_weights": books["day_weights"], "tank_start": "50 % of tank-capacity (Assumed, D-DD.19)",
            "declared_draw": "month unexplained_l in equal daily parts at 02:00 local (D-DD.19)",
            "fuel_notes": books["fuel_notes"], "critical_load_order": list(CRITICAL_ORDER),
            **_month_without_books(run, books)},
        "mappings": run.mappings, "golden_digests": golden}


def _month_without_books(run: SiteRun, books: dict) -> dict:
    """D-DD.103's condition, written when the run's span reaches a month with no books."""
    rates = sorted({books["months"][m]["rate_of"] for m in {d.strftime("%Y-%m") for d in run.days}
                    if "rate_of" in books["months"].get(m, {})})
    if not rates:
        return {}
    return {"month_without_books": {"rule": "D-DD.103", "load": "the rate month's kWh per weighted shape unit",
                                    "draw": "the rate month's daily parts by day of month", "rate_of": ", ".join(rates)}}


# --- the decided books ------------------------------------------------------------------------------------------------

def books_for(view: dict, history: dict, expenses: dict[str, str]) -> dict[str, dict]:
    """Per Site code: the months' delivered kWh and unexplained litres (history months from `history`, the accounting
    period from the view's period), the fuel notes of the tenant's expenses file (`expenses`, tenant slug to CSV
    text; rows of category Diesel), and the `demand` family's day weights. Mini-grid tenants only."""
    import csv
    import io

    families = view["history"]["families"]["demand"]["day"]
    weights = {"classes": view["history"]["day_classes"], **{k: str(v) for k, v in families.items()}}
    surplus = view["history"]["families"]["solar_surplus"]
    sun_weights = {"seasons": dict(view["history"]["seasons"]), "classes": view["history"]["day_classes"],
                   "season": {k: str(v) for k, v in surplus["season"].items()},
                   "day": {k: str(v) for k, v in surplus["day"].items()}}
    accounting = view["accounting_period"]
    out: dict[str, dict] = {}
    for tenant in view["tenants"]:
        if tenant.get("vertical") != "MINI_GRID":
            continue
        slug = tenant["tenant"]
        if slug not in expenses:  # D-DD.129: a mini-grid tenant's expenses file is required, never assumed empty
            raise TelemetryRefused("TEL_BOOKS", f"{slug} has no expenses file")
        notes: dict[str, list[dict]] = {}
        for row in csv.DictReader(io.StringIO(expenses[slug])):
            if row["Category"] == "Diesel":
                notes.setdefault(row["Site"], []).append({"at": row["Date"], "litres": int(row["Litres"])})
        for site in tenant["sites"]:
            months = {}
            for month, block in history["tenants"][slug][site["site"]].items():
                months[month] = {"delivered_kwh": block["actual"]["delivered_kwh"],
                                 "unexplained_l": block["actual"].get("unexplained_l", 0)}
            actual = site["period"]["actual"]
            months[accounting] = {"delivered_kwh": actual["delivered_kwh"], "unexplained_l": actual.get("unexplained_l", 0)}
            for month in _months_without_books(accounting):
                months[month] = {"rate_of": accounting,
                                 "delivered_kwh": _rate_kwh(month, accounting, weights, actual["delivered_kwh"])}
            out[site["code"]] = {"months": months, "day_weights": weights, "sun_weights": sun_weights,
                                 "fuel_notes": sorted(notes.get(site["code"], []), key=lambda n: n["at"])}
    return out


def _months_without_books(accounting: str) -> list[str]:
    """The months of `READINGS_SPAN` after the accounting period (D-DD.103)."""
    days, _minute = span_days(*READINGS_SPAN)
    return sorted({d.strftime("%Y-%m") for d in days if d.strftime("%Y-%m") > accounting})


def _rate_kwh(month: str, rate_of: str, weights: dict, delivered: int) -> int:
    """D-DD.103: E = round_half_even(k x sum over the month's span days of W(d) x sum of S(h) over the span's hours),
    k = the rate month's kWh per weighted shape unit."""
    classes = weights["classes"]

    def units(day: date, hours: range) -> Fraction:
        shape = sum(LOAD_SHAPE_KW[feeder][hour] for feeder in LOAD_SHAPE_KW for hour in hours)
        return Fraction(weights[day_class(day, classes)]) * shape

    k = Fraction(delivered) / sum((units(d, range(24)) for d in _month_days(rate_of)), Fraction(0))
    exact = k * sum((units(d, _span_hours(d)) for d in _month_days(month)), Fraction(0))
    return int((Decimal(exact.numerator) / Decimal(exact.denominator)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def _written(value: object) -> object:
    """A measured value as `measured.json` holds it: exact decimal text (`_decimal`, rounded once), maps sorted."""
    if isinstance(value, dict):
        return {k: _written(v) for k, v in sorted(value.items())}
    return _decimal(value)


def measured_for(slug: str, runs: list) -> dict:
    """`<slug>/telemetry/measured.json` (D-DD.99): per Site and month, each run's `measured_months()` with its
    vertical's fixed key set (mini-grid: the load energy the meters carried and the unserved energy the pack's accepted
    loads record; cold: the room meter; EV: bands, demand, import), and, for a tenant with EV Sites only, `departures`
    sorted by (site, departure instant, vehicle)."""
    sites, departures, ev = {}, [], False
    for run in runs:
        months = {month: _written(row) for month, row in run.measured_months().items()}
        end = run.end_local
        if (end.day, end.hour, end.minute) != (1, 0, 0):  # the span ends inside its last month (D-DD.99)
            months[run.days[-1].strftime("%Y-%m")]["partial_to"] = end.isoformat()
        sites[run.code] = months
        if hasattr(run, "departures"):
            ev = True
            departures += [{"site_code": d["site_code"], "vehicle_ref": d["vehicle_ref"], "block_ref": d["block_ref"],
                            "service_day": d["service_day"],
                            "departure_at": d["departure_at"].astimezone(run.zone).isoformat(),
                            "required_kwh": _decimal(d["required_kwh"]), "kwh_at_departure": _decimal(d["delivered_kwh"])}
                           for d in run.departures()]
    out = {"schema": "assetops.world-measured/1", "tenant": slug, "sites": sites}
    if ev and departures:  # no file writes an empty list (D-DD.99)
        out["departures"] = sorted(departures, key=lambda d: (d["site_code"], d["departure_at"], d["vehicle_ref"]))
    return out


def _vertical_runs() -> dict:
    """D-DD.123 `VERTICAL_RUNS`: the run class of each vertical family, one table. Read through the module's
    `__getattr__` because the vertical modules import this frame."""
    from .telemetry_cold import ColdSiteRun
    from .telemetry_ev import EvSiteRun

    return {"cold-thermal": ColdSiteRun, "ev-charger": EvSiteRun}


def __getattr__(name: str):
    if name == "VERTICAL_RUNS":
        return _vertical_runs()
    raise AttributeError(name)
