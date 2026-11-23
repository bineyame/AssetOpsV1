"""DD4.3 (spec `specs/DD-demo-data/spec.md` §4.5; D-DD.23, D-DD.25, D-DD.81, D-DD.87; `DD4b-preflight.md` Q1-Q15):
one EV depot's readings run on D-DD.81's day-level protocol.

`EvSiteRun(site, books, first, last)` drives one `ev-charger/1` pack per charger (`max_plugs=None`, pre-flight Q1;
`site_limit_kw` = the charger rating) over the local days `first..last`, one continuous execution advanced one local
day at a time (D-DD.69). It does not map `source_id`, round, write bytes or build a manifest: the frame
(`world/telemetry.py`, DD3a) does, at the join.

- `site`: the Site's `F` entry (D-DD.28): `code`, `timezone`, `foundation.components` in declared order (the feed's
  `ev-site-import-limit`; each `EV_CHARGER`'s `ev-charger-max-power`; its two `EV_CONNECTOR`s `<charger>-c1`,
  `<charger>-c2` with `ev-connector-max-power`).
- `books`:
  - `roster`: the Site's FLEET_ROSTER records (`exports_ev.roster_rows`, 1 Jul to 6 Nov);
  - `practice`: month -> `p_m` text (Embakasi; empty elsewhere: every bus plugs in at its return);
  - `faults`: `{"asset", "at", "source"}` from `M`'s incident blocks: a charger id faults both its connectors, a
    connector id faults one;
  - `clock`: `{"charger", "day", "minutes", "source"}` (CLOCK-1): the n-th charger in declared order.
- The minute (UTC), for the depot:
  1. departures (`UNPLUG`; a waiting bus leaves), then faults (`FAULT`; an aborted bus rejoins the queue with its
     remaining need, pre-flight Q7), then plug-ins join the queue in (plug-in instant, roster row) order;
  2. each queued bus takes the lowest declared connector that is UNPLUGGED, enabled and unfaulted at the minute's
     start (`PLUG session-<n>`, `AUTHORIZE ACCEPT`; charging from the next minute);
  3. the depot manager shares `ev-site-import-limit` in 1 kW round-robin quanta with a persistent pointer across the
     connectors that charge this minute, in (charger, connector) declared order, each capped by its connector
     rating, its charger's rating left and its bus's remaining need x 60 kW (pre-flight Q6); a changed share is
     passed to that charger's pack as `REQUEST_KW`.
- Public rows (pre-flight Q4): ev-publication/1's record set, written here: `state` every minute per connector,
  `session-event` and `fault-event` at their minute, `energy` (5-minute `INTERVAL_DELTA` of the meter rounded
  half-even to 0.001 at both ends, per started session), `power`, `requested-power`, `allocated-limit` (5-minute
  `INTERVAL_MEAN`, split at the connector's session boundaries) and the depot `import` (split at every connector's
  session boundaries). `device_id` is the bound asset (`ch-k1-c1`, `site-meter`), `signal_id` the channel.
- CLOCK-1 (pre-flight Q12): on its local day, every row of the charger's connectors whose start minute holds a
  session carries `start` and `end` the declared minutes later; the true minute drives the physics.
- Refusals are the frame's `TelemetryRefused` (D-DD.81's join): `TEL_FOUNDATION`, `TEL_EVENT_UNPLACED`, `TEL_PACK`.
- Rows are D-DD.91's seven elements plus `session`; an event's object adds `session_id` and `connector_id` where the
  pack gives a session (D-DD.123), and a connector measurement row inside a session carries the same pair as its
  `session` (D-DD.161; the depot import and rows outside a session carry None). `last` may be a local end instant
  (D-DD.103).

Standard library and the simulator's EV pack only.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

from ..packs.errors import PhysicallyUnacceptable
from ..packs.ev_charger import CONNECTORS, EvChargerPack, EvForcingRow, EvParameters, EvState
from .telemetry import TelemetryRefused, span_days

UTC = timezone.utc
STEP = timedelta(minutes=1)
SLOT = timedelta(minutes=5)
MINUTES_PER_HOUR = 60
SHARE_STEP_KW = Fraction(1)  # the load manager's share step (the pack's grant step), not a rounding quantum
LATE_PLUG = time(22, 0)  # spec §4.5: the rest plug in at 22:00
#: D-DD.98: a full bus is unplugged for a waiting one, which plugs in on that connector this many minutes later.
ROTATION_MINUTES = 5
#: D-DD.158: the EV month's hour windows, local-clock minutes [from, to) of each day (D-DD.20's `kwh_2200_2400`,
#: `kwh_0000_0500`).
HOUR_WINDOWS = (("2200_2400", 22 * 60, 24 * 60), ("0000_0500", 0, 5 * 60))
ROTATION_MINUTES_DELTA = timedelta(minutes=ROTATION_MINUTES)
#: Spec §4.5 plug-in practice at Embakasi, July to October; November keeps October's (pre-flight Q14, parity test).
PRACTICE = {"2026-07": "0.36", "2026-08": "0.43", "2026-09": "0.49", "2026-10": "0.55", "2026-11": "0.55"}
SITE_METER = "site-meter"
_SESSION_KIND = {"START": "EV_SESSION_START STARTED", "END": "EV_SESSION_END COMPLETED",
                 "ABORT": "EV_SESSION_ABORT ABORTED"}
_FAULT_KIND = {"FAULT": "EV_CONNECTOR_FAULT FAULTED", "CLEAR": "EV_CONNECTOR_CLEAR CLEARED"}
_MEANS = (("power", "allocated_kw"), ("requested-power", "requested_kw"), ("allocated-limit", "allocated_kw"))


def _refuse(code: str, detail: str) -> TelemetryRefused:
    return TelemetryRefused(code, detail)


def _kw(value: object, where: str) -> Fraction:
    try:
        out = Fraction(Decimal(str(value)))
    except (ArithmeticError, ValueError) as exc:
        raise _refuse("TEL_FOUNDATION", f"{where} {value!r} is not a number") from exc
    if out < 0:
        raise _refuse("TEL_FOUNDATION", f"{where} {value!r} is negative")
    return out


def _milli(value: Fraction) -> Fraction:
    """The meter's cumulative kWh, rounded half-even to 0.001 (ev-publication/1)."""
    q = (Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal("0.001"), rounding=ROUND_HALF_EVEN)
    return Fraction(q)


def round_half_even(value: Fraction) -> int:
    return int((Decimal(value.numerator) / Decimal(value.denominator)).to_integral_value(rounding=ROUND_HALF_EVEN))


class _Bus:
    __slots__ = ("ref", "block", "night", "order", "plug_at", "departure", "required", "delivered", "connector",
                 "plugged_at")

    def __init__(self, row: dict, order: int, plug_at: datetime) -> None:
        body = row["body"]
        self.ref, self.block = body["vehicle_ref"], body["block_ref"]
        self.night = row["clocks"]["effective_from"]
        self.order = order
        self.plug_at = plug_at
        self.departure = datetime.fromisoformat(body["departure_at"]).astimezone(UTC)
        self.required = Fraction(Decimal(body["required_kwh"]))
        self.delivered = Fraction(0)
        self.connector: tuple[int, str] | None = None
        self.plugged_at: datetime | None = None


class EvSiteRun:
    """One EV depot, one continuous execution of its chargers' packs over `first..last` (local days)."""

    def __init__(self, site: dict, books: dict, first: str, last: str) -> None:
        self.code = site["code"]
        self.zone = ZoneInfo(site["timezone"])
        self._foundation(site)
        self.days, end_minute = span_days(first, last)  # `last` a local day or a local end instant (D-DD.103)
        self.start = self._utc(self.days[0])
        self.end = self._utc(self.days[-1]) + timedelta(minutes=end_minute)
        if self.end - self.start != timedelta(minutes=(len(self.days) - 1) * 1440 + end_minute):
            raise _refuse("TEL_FOUNDATION", f"{self.code} a clock change inside {first}..{last}")
        self._conditions: list[dict] = [
            {"condition": "initial state", "value": "every connector UNPLUGGED; no bus at the depot before its first "
             "roster return", "source": "DD4b-preflight Q11 (Assumed)"},
            {"condition": "fault under a charging bus", "value": "the aborted bus rejoins the queue at the fault "
             "minute with its remaining need", "source": "DD4b-preflight Q7 (Assumed)"},
            {"condition": "rotation", "value": f"at the first minute a bus waits and a plugged bus has its required_kwh, "
             f"the full bus UNPLUGs and stays parked to its departure; the longest-waiting bus plugs in on that connector "
             f"{ROTATION_MINUTES} minutes later", "source": "D-DD.98 (Assumed attendant handling)"}]
        self.practice = {m: Fraction(Decimal(v)) for m, v in books.get("practice", {}).items()}
        if any(r["body"]["vehicle_ref"].endswith("-S01") and r["site_code"] == self.code
               for r in books.get("roster", [])):
            self._conditions.append({"condition": "spare arrival", "value": "the spare arrives at 10:00 local on its "
                                     "night's start date, plugs in on arrival and charges on idle daytime connectors",
                                     "source": "D-DD.98 (Assumed)"})
        if self.practice:
            self._conditions.append({"condition": "plug-in practice", "value": " ".join(
                f"{m}={v}" for m, v in sorted(books["practice"].items())), "source": "spec §4.5 (D-DD.23)"})
        self._buses = self._roster(books.get("roster", []))
        self._faults = self._fault_rows(books.get("faults", []))
        self._clock = self._clock_rows(books.get("clock", []))
        self.packs = [EvChargerPack(self._params(c), scenario_sha256=self._scenario(c["id"]), max_plugs=None)
                      for c in self.chargers]
        self.states = [EvState.initial(self.start) for _ in self.chargers]
        self.ordinals = [0] * len(self.chargers)
        self.pointer = 0
        self.queue: list[_Bus] = []
        self.on: dict[tuple[int, str], _Bus] = {}
        self.requests: dict[tuple[int, str], Fraction] = {}
        self.parked: list[_Bus] = []  # full buses rotated off their connector (D-DD.98)
        self.reserved: dict[tuple[int, str], tuple[_Bus, datetime]] = {}  # connector -> (waiting bus, plug instant)
        self._unplugs: list[tuple[datetime, str, str]] = []  # rotation UNPLUGs: (instant, bus, connector asset)
        self.advanced = 0
        self._records: dict[date, list[tuple]] = {}
        self._ordinals: dict[tuple[str, str], int] = {}
        self._episodes: dict[str, int] = {}
        self._departed: list[dict] = []
        self._plugs: list[tuple[datetime, str, str, str]] = []  # (instant, bus, connector asset, night)
        self._import: dict[datetime, Fraction] = {}
        self._charger_draw: dict[tuple[str, datetime], Fraction] = {}
        self._tariffs = list(books.get("tariffs", []))

    # -- inputs -------------------------------------------------------------------------------------------------------

    def _utc(self, day: date, at: time = time(0, 0)) -> datetime:
        return datetime.combine(day, at, tzinfo=self.zone).astimezone(UTC)

    def _foundation(self, site: dict) -> None:
        components = site["foundation"]["components"]

        def prop(c: dict, key: str) -> Fraction:
            values = [p["value"] for p in c.get("properties", []) if p["property_key"] == key]
            if len(values) != 1:
                raise _refuse("TEL_FOUNDATION", f"{self.code} {c['id']} {key}")
            return _kw(values[0], f"{self.code} {c['id']} {key}")

        feeds = [c for c in components if any(p["property_key"] == "ev-site-import-limit"
                                               for p in c.get("properties", []))]
        if len(feeds) != 1:
            raise _refuse("TEL_FOUNDATION", f"{self.code} ev-site-import-limit")
        self.import_limit = prop(feeds[0], "ev-site-import-limit")
        self.chargers = [c for c in components if c["type"] == "EV_CHARGER"]
        if not self.chargers:
            raise _refuse("TEL_FOUNDATION", f"{self.code} no EV_CHARGER")
        self.charger_kw: list[Fraction] = []
        self.connector_kw: list[Fraction] = []
        by_id = {c["id"]: c for c in components if c["type"] == "EV_CONNECTOR"}
        for c in self.chargers:
            self.charger_kw.append(prop(c, "ev-charger-max-power"))
            ratings = []
            for name in CONNECTORS:
                connector = by_id.get(f"{c['id']}-{name}")
                if connector is None:
                    raise _refuse("TEL_FOUNDATION", f"{self.code} {c['id']}-{name} is not declared")
                ratings.append(prop(connector, "ev-connector-max-power"))
            if len(set(ratings)) != 1:
                raise _refuse("TEL_FOUNDATION", f"{self.code} {c['id']} connector ratings differ")
            self.connector_kw.append(ratings[0])
        self.slots = [(k, name) for k in range(len(self.chargers)) for name in CONNECTORS]

    def _params(self, charger: dict) -> EvParameters:
        k = self.chargers.index(charger)
        return EvParameters(site_limit_kw=self.charger_kw[k], base_load_kw=Fraction(0),
                            connector_rating_kw=self.connector_kw[k], charger_rating_kw=self.charger_kw[k],
                            enabled_from=time(0, 0), enabled_to=time.max)  # pre-flight Q2: no schedule declared

    def _scenario(self, charger: str) -> str:
        return hashlib.sha256(f"assetops.world-ev/1|{self.code}|{charger}".encode()).hexdigest()  # pre-flight Q13

    def asset(self, slot: tuple[int, str]) -> str:
        return f"{self.chargers[slot[0]]['id']}-{slot[1]}"

    def _roster(self, rows: list[dict]) -> list[_Bus]:
        nights: dict[str, list[dict]] = {}
        for r in rows:
            if r["site_code"] == self.code:
                nights.setdefault(r["clocks"]["effective_from"], []).append(r)
        out: list[_Bus] = []
        for night in sorted(nights):
            items = sorted(nights[night], key=lambda r: r["source_record_id"])
            back = {r["source_record_id"]: datetime.fromisoformat(r["body"]["return_at"]).astimezone(UTC)
                    for r in items}
            if min(back.values()) < self.start or min(back.values()) >= self.end:
                continue  # the night is outside the span (no bus before its first return, Q11)
            plug = dict(back)
            p_m = self.practice.get(night[:7])
            if p_m is not None:
                early = round_half_even(len(items) * p_m)
                ordered = sorted(items, key=lambda r: (back[r["source_record_id"]], r["source_record_id"]))
                late = self._utc(date.fromisoformat(night), LATE_PLUG)
                for r in ordered[early:]:
                    plug[r["source_record_id"]] = max(late, back[r["source_record_id"]])
            for r in items:
                out.append(_Bus(r, len(out), plug[r["source_record_id"]]))
        return out

    def _instant(self, text: str, what: str) -> datetime:
        at = datetime.fromisoformat(text).astimezone(UTC)
        if at.second or at.microsecond or not self.start <= at < self.end:
            raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} {what} {text}")
        return at

    def _fault_rows(self, faults: list[dict]) -> dict[datetime, list[tuple[int, str]]]:
        out: dict[datetime, list[tuple[int, str]]] = {}
        ids = [c["id"] for c in self.chargers]
        for f in faults:
            at = self._instant(f["at"], f"fault {f['asset']}")
            asset = f["asset"].lower()
            if asset in ids:
                slots = [(ids.index(asset), name) for name in CONNECTORS]
            else:
                charger, _, name = asset.rpartition("-")
                if charger not in ids or name not in CONNECTORS:
                    raise _refuse("TEL_FOUNDATION", f"{self.code} fault on {f['asset']} names no charger or connector")
                slots = [(ids.index(charger), name)]
            out.setdefault(at, []).extend(slots)
            self._conditions.append({"condition": "fault", "value": f"{asset} FAULT at {f['at']}, no CLEAR in the "
                                     "span", "source": f["source"]})
        return out

    def _clock_rows(self, clock: list[dict]) -> dict[date, tuple[int, timedelta]]:
        out: dict[date, tuple[int, timedelta]] = {}
        for c in clock:
            k = int(c["charger"]) - 1
            if not 0 <= k < len(self.chargers):
                raise _refuse("TEL_FOUNDATION", f"{self.code} CLOCK-1 names charger {c['charger']}")
            day = date.fromisoformat(c["day"])
            if day not in self.days:
                raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} CLOCK-1 {c['day']}")
            out[day] = (k, timedelta(minutes=int(c["minutes"])))
            self._conditions.append({"condition": "CLOCK-1", "value": f"{self.chargers[k]['id']} session readings on "
                                     f"{c['day']} stamped {c['minutes']} minutes after the true minute",
                                     "source": c["source"]})
        return out

    # -- the minute ---------------------------------------------------------------------------------------------------

    def _share(self, charging: list[tuple[int, str]]) -> dict[tuple[int, str], Fraction]:
        caps = {s: min(self.connector_kw[s[0]], (self.on[s].required - self.on[s].delivered) * MINUTES_PER_HOUR)
                for s in charging}
        left = {k: self.charger_kw[k] for k in {s[0] for s in charging}}
        share = {s: Fraction(0) for s in charging}
        remaining = self.import_limit
        index = {s: i for i, s in enumerate(self.slots)}
        live = sorted(charging, key=index.__getitem__)
        n = len(self.slots)
        while remaining > 0 and live:
            progressed = False
            for step in range(n):
                s = self.slots[(self.pointer + step) % n]
                if s not in share:
                    continue
                headroom = min(caps[s] - share[s], left[s[0]])
                if headroom > 0:
                    q = min(SHARE_STEP_KW, headroom, remaining)
                    share[s] += q
                    left[s[0]] -= q
                    remaining -= q
                    progressed = True
                    if remaining == 0:
                        self.pointer = (self.pointer + step + 1) % n
                        return share
            if not progressed:
                break
        return share

    def _minute(self, t: datetime) -> None:
        forcing: list[list[EvForcingRow]] = [[] for _ in self.chargers]
        busy: set[tuple[int, str]] = set()
        # 1. departures
        for s, bus in list(self.on.items()):
            if bus.departure <= t:
                state = self.states[s[0]].connector(s[1]).state
                if state != "FAULTED":
                    forcing[s[0]].append(EvForcingRow(t, "UNPLUG", s[1], "END"))
                    busy.add(s)
                self._leave(bus, t)
                del self.on[s]
                self.requests.pop(s, None)
        for bus in [b for b in self.queue if b.departure <= t] + [b for b in self.parked if b.departure <= t]:
            (self.queue if bus in self.queue else self.parked).remove(bus)
            self._leave(bus, t)
        for s, (bus, _at) in list(self.reserved.items()):
            if bus.departure <= t:
                del self.reserved[s]
                self._leave(bus, t)
        # faults
        for s in self._faults.get(t, ()):
            forcing[s[0]].append(EvForcingRow(t, "FAULT", s[1], "LATCH"))
            busy.add(s)
            bus = self.on.pop(s, None)
            self.requests.pop(s, None)
            if bus is not None:
                bus.connector = None
                bus.plug_at = t
                self.queue.append(bus)
            held = self.reserved.pop(s, None)
            if held is not None:  # its connector faulted before the plug: the bus waits again
                self.queue.append(held[0])
        # plug-ins join the queue
        while self._next < len(self._arrivals) and self._arrivals[self._next].plug_at <= t:
            self.queue.append(self._arrivals[self._next])
            self._next += 1
        self.queue.sort(key=lambda b: (b.plug_at, b.order))
        # 2. connector assignment: a connector held for a rotated-in bus first (D-DD.98), then the queue
        due = [(s, bus) for s, (bus, at) in self.reserved.items() if at <= t]
        for s, bus in sorted(due, key=lambda x: self.slots.index(x[0])):
            del self.reserved[s]
            self._plug(s, bus, t, forcing, busy)
        for bus in list(self.queue):
            free = next((s for s in self.slots if s not in busy and s not in self.on and s not in self.reserved
                         and self.states[s[0]].connector(s[1]).state == "UNPLUGGED"), None)
            if free is None:
                break
            self.queue.remove(bus)
            self._plug(free, bus, t, forcing, busy)
        # rotation (D-DD.98): a waiting bus takes the connector of a full one, ROTATION_MINUTES later
        for bus in list(self.queue):
            full = next((s for s in self.slots if s in self.on and s not in busy and s not in self.reserved
                         and self.on[s].delivered >= self.on[s].required
                         and self.states[s[0]].connector(s[1]).state != "FAULTED"), None)
            if full is None:
                break
            forcing[full[0]].append(EvForcingRow(t, "UNPLUG", full[1], "END"))
            busy.add(full)
            gone = self.on.pop(full)
            self.requests.pop(full, None)
            gone.connector = None
            self.parked.append(gone)
            self._unplugs.append((t, gone.ref, self.asset(full)))
            self.queue.remove(bus)
            self.reserved[full] = (bus, t + ROTATION_MINUTES_DELTA)
        # 3. the depot manager
        self._manage(t, forcing, busy)

    def _plug(self, free: tuple[int, str], bus: _Bus, t: datetime, forcing: list, busy: set) -> None:
        k = free[0]
        state = self.states[k]
        label = f"session-{state.plugs + 1 + sum(1 for f in forcing[k] if f.kind == 'PLUG')}"
        forcing[k] += [EvForcingRow(t, "PLUG", free[1], label), EvForcingRow(t, "AUTHORIZE", free[1], "ACCEPT")]
        busy.add(free)
        self.on[free] = bus
        bus.connector = free
        bus.plugged_at = t
        self._plugs.append((t, bus.ref, self.asset(free), bus.night))

    def _manage(self, t: datetime, forcing: list, busy: set) -> None:
        charging = []
        for s, bus in self.on.items():
            if s in busy:
                continue
            c = self.states[s[0]].connector(s[1])
            if c.state == "CHARGING" or (c.state == "AUTHORIZING" and c.authorized_at is not None and c.authorized_at < t):
                charging.append(s)
        share = self._share(charging) if charging else {}
        for s in self.on:
            want = share.get(s, Fraction(0))
            if self.requests.get(s, Fraction(0)) != want:
                forcing[s[0]].append(EvForcingRow(t, "REQUEST_KW", s[1], _decimal(want)))
                self.requests[s] = want
        # the packs
        rank = {"PLUG": 0, "AUTHORIZE": 1, "REQUEST_KW": 2, "FAULT": 3, "CLEAR": 4, "UNPLUG": 5}
        total = Fraction(0)
        for k, pack in enumerate(self.packs):
            rows = tuple(sorted(forcing[k], key=lambda f: (CONNECTORS.index(f.connector), rank[f.kind])))
            first = self.ordinals[k]
            minute = pack.step(self.states[k], rows, ordinals=tuple(range(first, first + len(rows))))
            self.ordinals[k] += len(rows)
            self._docs[k].append(minute.document)
            self._events[k] += list(minute.events)
            for c in minute.document["connectors"]:
                s = (k, c["connector"])
                kw = Fraction(c["allocated_kw"])
                if kw and s in self.on:
                    self.on[s].delivered += kw / MINUTES_PER_HOUR
            draw = Fraction(minute.document["site_import_kw"])
            if draw:
                self._charger_draw[(self.chargers[k]["id"], t)] = draw
            total += draw
            self.states[k] = minute.after
        if total > self.import_limit:
            raise PhysicallyUnacceptable(f"depot import {total} kW exceeds {self.import_limit} kW")
        if total:
            self._import[t] = total

    def _leave(self, bus: _Bus, t: datetime) -> None:
        self._departed.append({"site_code": self.code, "vehicle_ref": bus.ref, "block_ref": bus.block,
                               "service_day": bus.night, "departure_at": bus.departure, "required_kwh": bus.required,
                               "delivered_kwh": bus.delivered})

    # -- public rows --------------------------------------------------------------------------------------------------

    def _rows(self, day: date, day_start: datetime, day_end: datetime) -> list[tuple]:
        rows: list[tuple] = []
        minutes = [day_start + STEP * i for i in range(len(self._docs[0]))]
        cuts_all: set[datetime] = set()
        for k in range(len(self.chargers)):
            docs, events = self._docs[k], self._events[k]
            per = {name: [next(c for c in d["connectors"] if c["connector"] == name) for d in docs]
                   for name in CONNECTORS}
            closing = {name: self.states[k].connector(name) for name in CONNECTORS}
            for name in CONNECTORS:
                device = self.asset((k, name))
                for i, t in enumerate(minutes):
                    rows.append((device, "state", t, t, per[name][i]["state"], "state", None,
                                 per[name][i]["session_id"]))
                spans = list(self._spans[(k, name)])
                for e in events:
                    if e.connector != name:
                        continue
                    if e.kind in _SESSION_KIND:
                        rows.append((device, "session-event", e.at, e.at, None, "event",
                                     self._event(device, "session-event", _SESSION_KIND[e.kind], e.session_id, None),
                                     e.session_id))
                        if e.kind == "START":
                            spans.append([e.at, None, e.session_id])
                        else:
                            open_span = next(sp for sp in spans if sp[2] == e.session_id and sp[1] is None)
                            open_span[1] = e.at
                    else:
                        if e.kind == "FAULT":
                            self._episodes[device] = self._episodes.get(device, 0) + 1
                        rows.append((device, "fault-event", e.at, e.at, None, "event",
                                     self._event(device, "fault-event", _FAULT_KIND[e.kind], e.session_id,
                                                 ["fault", self._episodes.get(device, 0)]), e.session_id))
                cuts = {t for sp in spans for t in sp[:2] if t is not None and day_start < t < day_end}
                cuts_all |= cuts

                def energy(t: datetime) -> Fraction:
                    i = int((t - day_start) / STEP)
                    return Fraction(per[name][i]["energy_kwh"]) if i < len(minutes) else closing[name].energy_kwh

                slot = day_start
                while slot < day_end:
                    for a, b in _split(slot, slot + SLOT, cuts):
                        for s0, s1, session in spans:
                            if s0 <= a and (s1 is None or b <= s1):
                                rows.append((device, "energy", a, b, _milli(energy(b)) - _milli(energy(a)), "kWh",
                                             None, session))
                        ia, ib = int((a - day_start) / STEP), int((b - day_start) / STEP)
                        for channel, key in _MEANS:
                            mean = sum((Fraction(per[name][i][key]) for i in range(ia, ib)), Fraction(0)) / (ib - ia)
                            rows.append((device, channel, a, b, mean, "kW", None, per[name][ia]["session_id"]))
                    slot += SLOT
                self._spans[(k, name)] = [sp for sp in spans if sp[1] is None]
            self._docs[k], self._events[k] = [], []
        slot = day_start
        while slot < day_end:
            for a, b in _split(slot, slot + SLOT, cuts_all):
                mean = sum((self._import.get(t, Fraction(0)) for t in minutes[int((a - day_start) / STEP):
                                                                           int((b - day_start) / STEP)]),
                           Fraction(0)) / int((b - a) / STEP)
                rows.append((SITE_METER, "import", a, b, mean, "kW", None, None))
            slot += SLOT
        shift = self._clock.get(day)
        out = []
        for row in rows:
            device, signal, a, b, value, unit, event, session = row
            if shift is not None and session is not None and device.startswith(f"{self.chargers[shift[0]]['id']}-"):
                a, b = a + shift[1], b + shift[1]
            # D-DD.161: a connector measurement row inside a session carries the session's pair, as its events do
            carried = None if event is not None or session is None else {"session_id": session, "connector_id": device}
            out.append((device, signal, a, b, value, unit, event, carried))
        return out

    def _event(self, device: str, signal: str, kind: str, session: str | None, correlation: list | None) -> dict:
        """D-DD.91's EVENT fields (ids formed at sealing), plus `session_id` and `connector_id` where the pack gives
        them (D-DD.123); `ordinal` is one-based per channel, continuous over the span."""
        record_kind, outcome = kind.split()
        key = (device, signal)
        self._ordinals[key] = self._ordinals.get(key, 0) + 1
        out = {"record_kind": record_kind, "outcome": outcome, "actor": "CONTROLLER", "component_id": device,
               "ordinal": self._ordinals[key], "correlation": None if session is not None else correlation}
        if session is not None:
            out["session_id"] = session
            out["connector_id"] = device
        return out

    # -- the protocol (D-DD.81) ---------------------------------------------------------------------------------------

    def advance_day(self) -> date:
        """Step one local day (1440 minutes) of every charger and keep its rows; returns the day."""
        if self.advanced >= len(self.days):
            raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} advanced past {self.days[-1].isoformat()}")
        if self.advanced == 0:
            self._arrivals = sorted(self._buses, key=lambda b: (b.plug_at, b.order))
            self._next = 0
            self._spans = {s: [] for s in self.slots}
        self._docs = [[] for _ in self.chargers]
        self._events = [[] for _ in self.chargers]
        self._charger_draw = {}  # the current day's only (DD4b run 5)
        day = self.days[self.advanced]
        day_start = self._utc(day)
        day_end = min(day_start + timedelta(days=1), self.end)  # the span's end instant (D-DD.103)
        t = day_start
        try:
            while t < day_end:
                self._minute(t)
                t += STEP
        except PhysicallyUnacceptable as exc:
            raise _refuse("TEL_PACK", f"{self.code} {day.isoformat()} {exc}") from exc
        self._records[day] = self._rows(day, day_start, day_end)
        self.advanced += 1
        return day

    def day_records(self, day: date) -> list[tuple]:
        """The day's pack rows `(device_id, signal_id, start, end, value, unit, event, session)`, UTC instants, exact
        values; `session` is `{"session_id", "connector_id"}` on a connector measurement row inside a session, else
        None (D-DD.161)."""
        if day not in self._records:
            raise _refuse("TEL_EVENT_UNPLACED", f"{self.code} {day.isoformat()} is not advanced")
        return sorted(self._records[day], key=lambda r: (r[2], r[3], r[0], r[1], r[6]["ordinal"] if r[6] else 0))

    def conditions(self) -> list[dict]:
        return list(self._conditions)

    def private_parameters(self) -> dict:
        return {"model": "ev-charger/1 (max_plugs None)", "import_limit_kw": str(self.import_limit),
                "share_step_kw": str(SHARE_STEP_KW), "late_plug": LATE_PLUG.isoformat(timespec="minutes"),
                "practice": {m: str(v) for m, v in sorted(self.practice.items())},
                "chargers": [{"id": c["id"], "charger_kw": str(self.charger_kw[k]),
                              "connector_kw": str(self.connector_kw[k])} for k, c in enumerate(self.chargers)]}

    # -- what the measured books and the plants read (exact; DD4.4 settles their shape) ----------------------------

    def departures(self) -> list[dict]:
        return list(self._departed)

    def unplugs(self) -> list[tuple[datetime, str, str]]:
        """The rotation UNPLUGs (D-DD.98): (instant, bus, connector asset)."""
        return list(self._unplugs)

    def plug_ins(self, night: str) -> list[tuple[datetime, str]]:
        return [(t, bus) for t, bus, _, n in self._plugs if n == night]

    def assignments(self, night: str) -> list[tuple[datetime, str, str]]:
        return [(t, bus, asset) for t, bus, asset, n in self._plugs if n == night]

    def release_day(self, day: date) -> None:
        """Drop a day's rows once the frame has written them (DD4b run 5: one day held at a time)."""
        self._records.pop(day, None)

    @property
    def end_local(self) -> datetime:
        """The span's end instant, local time (D-DD.103)."""
        return self.end.astimezone(self.zone)

    def _bands_on(self, day: date) -> list[tuple[str, int, int]]:
        """The price classes of the TARIFF_SCHEDULE in force on a local day: (class, from minute, to minute). The class
        is the band name before `-` (D-DD.61: OFFPEAK-AM and OFFPEAK-PM are OFFPEAK)."""
        text = day.isoformat()
        found = [r for r in self._tariffs if r["clocks"]["effective_from"] <= text
                 and text <= r["clocks"].get("effective_to", "9999-12-31")]
        if len(found) != 1:
            raise _refuse("TEL_BOOKS", f"{self.code} {text} has {len(found)} TARIFF_SCHEDULE records in force")

        def minute(hhmm: str) -> int:
            hours, minutes = hhmm.split(":")
            return int(hours) * MINUTES_PER_HOUR + int(minutes)

        return [(b["band"].split("-")[0], minute(b["from"]), minute(b["to"])) for b in found[0]["body"]["bands"]]

    def measured_months(self) -> dict[str, dict]:
        """D-DD.99 EV `<month>`: `{"bands": {class: kWh}, "demand_kw", "import_kwh", "windows"}` from the depot import
        by minute, exact (the frame rounds once). Every class of the schedules in force that month is present;
        `demand_kw` is the largest mean of the 30 minutes from each :00 and :30; `windows` (D-DD.158) sums the import
        over local minutes [22:00, 24:00) and [00:00, 05:00) of each day."""
        months: dict[str, dict] = {}
        windows: dict[datetime, Fraction] = {}
        for day in self.days:
            month = day.strftime("%Y-%m")
            entry = months.setdefault(month, {"bands": {}, "demand_kw": Fraction(0),
                                              "windows": {name: Fraction(0) for name, _, _ in HOUR_WINDOWS}})
            for name, _, _ in self._bands_on(day):
                entry["bands"].setdefault(name, Fraction(0))
        tables: dict[date, list[tuple[str, int, int]]] = {}
        for t, kw in sorted(self._import.items()):
            lt = t.astimezone(self.zone)
            day = lt.date()
            if day not in tables:
                tables[day] = self._bands_on(day)
            at = lt.hour * MINUTES_PER_HOUR + lt.minute
            name = next((n for n, a, b in tables[day] if a <= at < b), None)
            if name is None:
                raise _refuse("TEL_BOOKS", f"{self.code} {lt.isoformat()} is in no band of its TARIFF_SCHEDULE")
            bands = months[lt.strftime("%Y-%m")]["bands"]
            bands[name] += kw / MINUTES_PER_HOUR
            hour_windows = months[lt.strftime("%Y-%m")]["windows"]
            for window_name, a, b in HOUR_WINDOWS:
                if a <= at < b:
                    hour_windows[window_name] += kw / MINUTES_PER_HOUR
            window = lt.replace(minute=lt.minute - lt.minute % 30)
            windows[window] = windows.get(window, Fraction(0)) + kw
        for window, total in windows.items():
            entry = months[window.strftime("%Y-%m")]
            entry["demand_kw"] = max(entry["demand_kw"], total / 30)
        for entry in months.values():
            entry["bands"] = dict(sorted(entry["bands"].items()))
            entry["import_kwh"] = sum(entry["bands"].values(), Fraction(0))
        return dict(sorted(months.items()))

    def import_by_minute(self) -> dict[datetime, Fraction]:
        return dict(self._import)

    def charger_draw(self) -> dict[tuple[str, datetime], Fraction]:
        """The last advanced day's (charger, minute) draw, non-zero minutes only."""
        return dict(self._charger_draw)


# --- the EV books (D-DD.123) ------------------------------------------------------------------------------------------

#: The depots' faults (`M`'s incident blocks are outside the view, as D-DD.120's cold events); `test_dd4_ev_join` pins
#: them to `M`. Ruiru's instant within 6 Oct is the 14th bus's charge (pre-flight Q7, Assumed).
EV_FAULTS: dict[str, tuple[dict, ...]] = {
    "EV-KAS": ({"asset": "ch-k2", "at": "2026-11-01T23:40:00+03:00", "source": "M tenants.metro-bus.EV-KAS incident.fault"},),
    "EV-RUI": ({"asset": "ch-r7-c2", "at": "2026-10-06T00:00:00+03:00",
                "source": "M tenants.metro-bus.EV-RUI incident.fault (00:00 Assumed, DD4b-preflight Q7)"},),
}
#: CLOCK-1 (`M` `disorder_tests`, pre-flight Q12): the third charger in declared order, 4 minutes fast, on 15 Oct.
EV_CLOCK: dict[str, tuple[dict, ...]] = {
    "EV-EMB": ({"charger": 3, "day": "2026-10-15", "minutes": 4, "source": "M disorder_tests CLOCK-1"},)}
ROSTER_KEY = "profile.ev-fleet-roster"


def ev_roster_files(view: dict, history: dict, records) -> list:
    """Each EV tenant's roster `ExportFile`, from the same function the `exports` command runs (as D-DD.119's ledger)."""
    from .exports_ev import build_ev_exports

    out = []
    for tenant in view["tenants"]:
        if tenant.get("vertical") == "EV_DEPOT":
            out += [f for f in build_ev_exports(view, history, records, tenant).files if f.key == ROSTER_KEY]
    return out


def ev_books_for(view: dict, rosters: list) -> dict[str, dict]:
    """Per EV Site code: its roster rows, plug-in practice (Embakasi), faults, CLOCK-1 and TARIFF_SCHEDULE records."""
    from .tariffs import tariff_schedules

    schedules = tariff_schedules(view)
    rows = [r for f in rosters for r in f.records]
    out: dict[str, dict] = {}
    for tenant in view["tenants"]:
        if tenant.get("vertical") != "EV_DEPOT":
            continue
        tariffs = schedules.get(tenant["tenant"], {}).get("records", [])
        for site in tenant["sites"]:
            code = site["code"]
            out[code] = {"roster": [r for r in rows if r["site_code"] == code],
                         "practice": dict(PRACTICE) if code == "EV-EMB" else {},
                         "faults": list(EV_FAULTS.get(code, ())), "clock": list(EV_CLOCK.get(code, ())),
                         "tariffs": [t for t in tariffs if t["site_code"] == code]}
    return out


def _decimal(value: Fraction) -> str:
    """REQUEST_KW text: exact decimal when it terminates, else the exact fraction (the pack parses both)."""
    if value.denominator == 1:
        return str(value.numerator)
    q = Decimal(value.numerator) / Decimal(value.denominator)
    return format(q, "f") if Fraction(q) == value else f"{value.numerator}/{value.denominator}"


def _split(start: datetime, end: datetime, cuts: set[datetime]) -> list[tuple[datetime, datetime]]:
    points = [start] + sorted(c for c in cuts if start < c < end) + [end]
    return list(zip(points, points[1:]))


__all__ = ["EvSiteRun", "EV_CLOCK", "EV_FAULTS", "PRACTICE", "ROSTER_KEY", "ev_books_for", "ev_roster_files",
           "round_half_even"]
