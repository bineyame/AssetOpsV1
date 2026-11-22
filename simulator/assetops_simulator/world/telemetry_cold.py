"""DD4.2 (spec `specs/DD-demo-data/spec.md` §4.4; D-DD.81, D-DD.83, D-DD.85, D-DD.86, D-DD.87): one cold room's
readings run on D-DD.81's day-level protocol.

`ColdSiteRun(site, books, first, last)` drives cold-thermal 2 (`packs/cold.py`, `DD_LOAD_PARAMETERS`) over the local
days `first..last`, one continuous execution advanced one local day at a time (D-DD.69). It does not map
`source_id`, round, write bytes or build a manifest: the frame (`world/telemetry.py`, DD3a) does, at the join.

- `site`: the Site's `F` entry (D-DD.28): `code`, `timezone`, `foundation.components[].properties` (the thirteen
  cold-* Foundation values, text or number).
- `books`:
  - `ledger`: the Site's `STORAGE_MOVEMENT` records as the storage ledger exports them (D-DD.85 lots);
  - `cooling`: the manifest's `history.families.cooling` (`season`, `day`), `seasons` (month -> season) and
    `day_classes` (class -> ISO weekdays);
  - `efficiency`: month -> `f_m` as exact text (absent = 1; spec §4.4);
  - `events`: story forcings `{"kind", "at", "source"}` (`at` an ISO instant on a minute; D-DD.83's Thika
    sequence), read from `M` by the frame.
- Forcings (D-DD.85, D-DD.86): `CRATES_IN n`/`CRATES_OUT n` at each movement in the span; one door cycle
  (`DOOR_OPEN`, `DOOR_CLOSE` 5 minutes later) per movement instant; `AMBIENT` at 00:00 local of each day after the
  first; `EFFICIENCY` at 00:00 local of a month's first day when `f_m` changes, and at the first minute when it is
  not 1.
- Initial state (stated in `conditions`): the chamber at the room's control low, the first day's ambient, the crates
  of the movements before `first` (no field heat carried), generator STOPPED, grid AVAILABLE.
- Refusals are `ValueError`s whose message starts with the `TEL_*` code (D-DD.81: the frame's `TelemetryRefused`
  replaces them at the join): `TEL_FOUNDATION`, `TEL_EVENT_UNPLACED`, `TEL_PACK`.

Standard library and the simulator's cold pack only.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

from ..packs.cold import (DD_LOAD_PARAMETERS, FORCING_EFFECTS, PROPERTY_FIELDS, V2_FORCING_ASSETS, ColdForcingRow,
                          ColdPack, ColdParameters, ColdState)
from ..packs.errors import PhysicallyUnacceptable

STEP = timedelta(minutes=1)
DOOR_MINUTES = 5  # spec §4.4: door per movement
REFERENCE_AMBIENT = Fraction(24)  # M:430, degC
SENSITIVITY = Fraction(25, 1000)  # M:430, 2.5 % per degC
#: Story forcings the writer may place, with their pack asset and value.
EVENT_FORCINGS = {kind: effect for kind, effect in FORCING_EFFECTS.items() if kind != "PROBE_FAILURE"} | {
    "GENERATOR_HAND_START": ("generator-1", "RUNNING")}


def _refuse(code: str, detail: str) -> ValueError:
    return ValueError(f"{code} {detail}")


def _text(value: object) -> str:
    if isinstance(value, float):
        return format(Decimal(str(value)), "f")
    return str(value)


def _decimal_text(value: Fraction) -> str:
    """Exact decimal text of a Fraction with a terminating expansion (the day ambient)."""
    q = Decimal(value.numerator) / Decimal(value.denominator)
    if Fraction(q) != value:
        raise _refuse("TEL_FOUNDATION", f"ambient {value} has no exact decimal text")
    return format(q.normalize(), "f")


def cold_parameters(site: dict) -> ColdParameters:
    """The thirteen cold-* Foundation values of the Site (`TEL_FOUNDATION` if one is missing)."""
    found: dict[str, tuple[str, str]] = {}
    for component in site["foundation"]["components"]:
        for p in component.get("properties", []):
            if p["property_key"] in PROPERTY_FIELDS:
                if p["property_key"] in found:
                    raise _refuse("TEL_FOUNDATION", f"{site['code']} {p['property_key']} is declared twice")
                found[p["property_key"]] = (_text(p["value"]), p["unit"])
    missing = sorted(set(PROPERTY_FIELDS) - set(found))
    if missing:
        raise _refuse("TEL_FOUNDATION", f"{site['code']} {' '.join(missing)}")
    try:
        return ColdParameters.from_properties(found)
    except PhysicallyUnacceptable as exc:
        raise _refuse("TEL_FOUNDATION", f"{site['code']} {exc}") from exc


def day_ambient(day: date, cooling: dict, code: str) -> Fraction:
    """D-DD.86: 24 + (w_d - 1) / 0.025, w_d = the `cooling` family's season x day class, no jitter."""
    season = cooling["seasons"].get(day.strftime("%Y-%m"))
    if season is None:
        raise _refuse("TEL_FOUNDATION", f"{code} {day.isoformat()} has no declared season for the ambient")
    classes = [c for c, weekdays in cooling["day_classes"].items() if day.isoweekday() in weekdays]
    if len(classes) != 1:
        raise _refuse("TEL_FOUNDATION", f"{code} {day.isoformat()} is in {len(classes)} day classes")
    family = cooling["cooling"]
    weight = Fraction(str(family["season"][season])) * Fraction(str(family["day"][classes[0]]))
    return REFERENCE_AMBIENT + (weight - 1) / SENSITIVITY


class ColdSiteRun:
    """One cold room, one continuous cold-thermal 2 execution over `first..last` (local days), a day at a time."""

    def __init__(self, site: dict, books: dict, first: str, last: str) -> None:
        self.code = site["code"]
        self.zone = ZoneInfo(site["timezone"])
        self.params = cold_parameters(site)
        self.load = DD_LOAD_PARAMETERS
        self.pack = ColdPack(self.params, load=self.load)
        self.days = []
        day, end_day = date.fromisoformat(first), date.fromisoformat(last)
        while day <= end_day:
            self.days.append(day)
            day += timedelta(days=1)
        if not self.days:
            raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} the span {first}..{last} is empty")
        self.start = self._utc(self.days[0])
        self.end = self._utc(self.days[-1] + timedelta(days=1))
        if self.end - self.start != timedelta(days=len(self.days)):
            raise _refuse("TEL_FOUNDATION", f"{self.code} a clock change inside {first}..{last}")
        self.cooling = {"cooling": books["cooling"], "seasons": books["seasons"], "day_classes": books["day_classes"]}
        self.ambients = {d: day_ambient(d, self.cooling, self.code) for d in self.days}
        self.efficiency = {m: Fraction(v) for m, v in books.get("efficiency", {}).items()}
        self._conditions: list[dict] = []
        self.forcings, opening = self._forcings(books)
        initial = ColdState.initial(self.start, self.params.control_low, self.ambients[self.days[0]])
        self.state = ColdState(**{**initial.__dict__, "crates": opening})
        self._conditions.append({"condition": "initial state", "value": (
            f"chamber {self.params.control_low} degC (control low), ambient {_decimal_text(self.ambients[self.days[0]])}"
            f" degC, {opening} crates from movements before {self.days[0].isoformat()} (no field heat carried), "
            "generator STOPPED, grid AVAILABLE"), "source": "spec §4.4 (Assumed)"})
        self._conditions.append({"condition": "ambient", "value": "day-constant: 24 + (w_d - 1) / 0.025, w_d = cooling "
                                 "season x day class, no jitter", "source": "history.families.cooling (D-DD.86)"})
        self.advanced = 0
        self._records: dict[date, list[tuple]] = {}
        self._month_rounding: dict[str, Fraction] = {}

    # -- inputs ---------------------------------------------------------------------------------------------------

    def _utc(self, day: date, at: time = time(0, 0)) -> datetime:
        return datetime.combine(day, at, tzinfo=self.zone).astimezone(ZoneInfo("UTC"))

    def _f_m(self, month: str) -> Fraction:
        return self.efficiency.get(month, Fraction(1))

    def _forcings(self, books: dict) -> tuple[dict[datetime, list[ColdForcingRow]], int]:
        out: dict[datetime, list[ColdForcingRow]] = {}

        def put(at: datetime, kind: str, asset: str, value: str) -> None:
            out.setdefault(at, []).append(ColdForcingRow(at, kind, asset, value))

        opening = 0
        doors: set[datetime] = set()
        for r in books["ledger"]:
            if r["site_code"] != self.code:
                continue
            at = datetime.fromisoformat(r["clocks"]["occurred_at"]).astimezone(ZoneInfo("UTC"))
            n = int(r["quantity"]["value"])
            direction = r["body"]["direction"]
            if at < self.start:
                opening += n if direction == "IN" else -n
                continue
            if at >= self.end:
                continue
            put(at, "CRATES_IN" if direction == "IN" else "CRATES_OUT", "room-1", str(n))
            doors.add(at)
        if opening < 0:
            raise _refuse("TEL_PACK", f"{self.code} {opening} crates before {self.days[0].isoformat()}")
        for at in sorted(doors):  # one door cycle per movement instant (several batches leave at one 16:00)
            if at + STEP * DOOR_MINUTES >= self.end:
                raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} door close after the span at {at.isoformat()}")
            put(at, "DOOR_OPEN", "door-1", "OPEN")
            put(at + STEP * DOOR_MINUTES, "DOOR_CLOSE", "door-1", "CLOSED")
        for day in self.days[1:]:
            put(self._utc(day), "AMBIENT", V2_FORCING_ASSETS["AMBIENT"], _decimal_text(self.ambients[day]))
        before = Fraction(1)
        for day in self.days:
            if day == self.days[0] or day.day == 1:
                f = self._f_m(day.strftime("%Y-%m"))
                if f != before:
                    put(self._utc(day), "EFFICIENCY", V2_FORCING_ASSETS["EFFICIENCY"], str(f))
                before = f
        for e in books.get("events", []):
            if e["kind"] not in EVENT_FORCINGS:
                raise _refuse("TEL_PACK", f"{self.code} {e['kind']} is not a cold-thermal 2 story forcing")
            at = datetime.fromisoformat(e["at"]).astimezone(ZoneInfo("UTC"))
            if at.second or at.microsecond or not self.start <= at < self.end:
                raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} {e['kind']} {e['at']}")
            asset, value = EVENT_FORCINGS[e["kind"]]
            put(at, e["kind"], asset, value)
            self._conditions.append({"condition": e["kind"], "value": e["at"], "source": e["source"]})
        return out, opening

    # -- the protocol (D-DD.81) -------------------------------------------------------------------------------------

    def advance_day(self) -> date:
        """Step one local day (1440 minutes) and keep its pack rows; returns the day."""
        if self.advanced >= len(self.days):
            raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} advanced past {self.days[-1].isoformat()}")
        day = self.days[self.advanced]
        day_start = self._utc(day)
        day_end = day_start + timedelta(days=1)
        rows: list[tuple] = []
        state = self.state
        t = day_start
        try:
            while t < day_end:
                tr = self.pack.step(state, tuple(self.forcings.get(t, ())), start=self.start)
                for r in tr.records:
                    if r.measurement == "INTERVAL_MEAN" and r.interval_start < day_start:
                        continue  # the previous day's last interval, kept there by its closing read
                    rows.append(self._row(r))
                state = tr.after
                t += STEP
            # the day's last interval mean, read at the closing instant without applying the next day's forcings
            closing = self.pack.step(state, (), transition=False, start=self.start)
            rows += [self._row(r) for r in closing.records if r.measurement == "INTERVAL_MEAN"]
        except PhysicallyUnacceptable as exc:
            raise _refuse("TEL_PACK", f"{self.code} {day.isoformat()} {exc}") from exc
        month = day.strftime("%Y-%m")
        self._month_rounding[month] = self._month_rounding.get(month, Fraction(0)) + (
            state.rounding_total - self.state.rounding_total)
        self.state = state
        self._records[day] = rows
        self.advanced += 1
        return day

    @staticmethod
    def _row(r) -> tuple:
        if r.measurement is None:  # an event: its kind, outcome and actor as the value
            return (r.device_id, r.signal_id, r.source_time, r.source_time,
                    f"{r.record_kind} {r.outcome} {r.actor}", "event")
        start = r.interval_start if r.measurement == "INTERVAL_MEAN" else r.source_time
        return (r.device_id, r.signal_id, start, r.source_time, r.value, r.unit)

    def day_records(self, day: date) -> list[tuple]:
        """The day's pack rows `(device_id, signal_id, start, end, value, unit)`, UTC instants, exact values."""
        if day not in self._records:
            raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} {day.isoformat()} is not advanced")
        return sorted(self._records[day], key=lambda r: (r[2], r[3], r[0], r[1]))

    def conditions(self) -> list[dict]:
        return list(self._conditions)

    def private_parameters(self) -> dict:
        p = self.load
        return {
            "model": "cold-thermal/2", "respiration_kw_per_crate": str(p.respiration_kw_per_crate),
            "field_heat_kwh_per_crate_degc": str(p.field_heat_kwh_per_crate_degc),
            "field_heat_minutes": p.field_heat_minutes, "field_heat_target_degc": str(p.field_heat_target_degc),
            "cop": str(p.cop), "auxiliary_kw": str(p.auxiliary_kw),
            "start_failure_at_request": p.start_failure_at_request,
            "temperature_quantum": str(p.temperature_quantum),
            "efficiency": {m: str(self._f_m(m)) for m in sorted({d.strftime("%Y-%m") for d in self.days})},
            "rounding_total_kwh": {m: str(v) for m, v in sorted(self._month_rounding.items())},
        }


__all__ = ["ColdSiteRun", "cold_parameters", "day_ambient", "EVENT_FORCINGS"]
