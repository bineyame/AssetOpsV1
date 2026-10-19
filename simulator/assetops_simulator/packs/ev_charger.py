"""The standalone EV charger pack, `ev-charger/1` (W2-05b; technical design section 3; build spec Q2, Q3, Q13, Q14).

Two declared connectors under one charger share the Site import limit. The pack is pure: no SQL, HTTP,
publication or accepted-evidence import. It steps exact rational arithmetic once per UTC minute.

## The minute (boundary `t`, covering `[t, t+1min)`)

1. Apply that boundary's forcing in `(connector rank, kind rank)` order (`c1 < c2`; PLUG, AUTHORIZE, REQUEST_KW,
   FAULT, CLEAR, UNPLUG) through the total state/forcing table (Q13). A refused cell raises
   `PhysicallyUnacceptable` before any new output; a no-op emits nothing.
2. Complete authorization: a connector still AUTHORIZING since an earlier boundary enters CHARGING and emits one
   START, so 08:00 authorization starts at 08:01 and a 08:01 REQUEST_KW supplies the first minute.
3. Allocate `available = max(0, site_limit - base_load)` (zero while the grid input is unavailable) in 1 kW
   round-robin quanta by connector ID with a persistent pointer, among CHARGING connectors only, each bounded by
   `min(request, connector rating, charger rating)` and the enable schedule. A non-CHARGING connector allocates 0.
4. Integrate `energy_next = energy + allocated_kW / 60` exactly, and check every invariant.

The closing boundary (`end`) is a snapshot: no forcing, no transition, no allocation. One private boundary document
per boundary (61 for a one-hour window) records both connectors' state, scoped session token, requested and
allocated kW, cumulative exact kWh and fault latch, the Site available/import kW and the forcing ordinal. Only
their digest leaves the pack with the events; private labels, requests and forcing never become public output.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import datetime, time, timedelta
from fractions import Fraction
from typing import Any

from assetops_simulator.packs.errors import PhysicallyUnacceptable

MODEL_PROFILE = ("ev-charger", 1)
STEP = timedelta(minutes=1)
MINUTES_PER_HOUR = Fraction(60)
QUANTUM_KW = Fraction(1)

CONNECTORS = ("c1", "c2")
CONNECTOR_STATES = ("UNPLUGGED", "PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED")
FORCING_KIND_RANK = {"PLUG": 0, "AUTHORIZE": 1, "REQUEST_KW": 2, "FAULT": 3, "CLEAR": 4, "UNPLUG": 5}
CONNECTOR_RANK = {connector: rank for rank, connector in enumerate(CONNECTORS)}
PLUG_LABELS = ("session-1", "session-2")
EVENT_KINDS = ("START", "END", "ABORT", "FAULT", "CLEAR")
_FIXED_VALUES = {"FAULT": "LATCH", "CLEAR": "CLEAR", "UNPLUG": "END"}


def canonical_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_text(value).encode("utf-8")).hexdigest()


def scoped_session_id(scenario_sha256: str, private_label: str) -> str:
    """Q3: `ev-` + lowercase SHA-256 of canonical `[scenario_sha256, "session", private_label]`, hashed once."""
    return "ev-" + _sha256([scenario_sha256, "session", private_label])


def exact_text(value: Fraction) -> str:
    """Exact private rendering: an integer as itself, otherwise `numerator/denominator`."""
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _instant(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class EvParameters:
    """Frozen Foundation values the pack reads (EV-LAB-001: 80 kW feed, 60 kW connectors/charger, base 0)."""

    site_limit_kw: Fraction
    base_load_kw: Fraction
    connector_rating_kw: Fraction
    charger_rating_kw: Fraction
    #: UTC time-of-day enable schedule `[enabled_from, enabled_to)`; outside it allocation pauses at 0.
    enabled_from: time
    enabled_to: time

    def __post_init__(self) -> None:
        for name in ("site_limit_kw", "base_load_kw", "connector_rating_kw", "charger_rating_kw"):
            value = getattr(self, name)
            if not isinstance(value, Fraction) or value < 0:
                raise PhysicallyUnacceptable(f"{name} {value} is not a nonnegative exact value")
        if not self.enabled_from < self.enabled_to:
            raise PhysicallyUnacceptable("the enable schedule does not start before it ends")


DEFAULT_PARAMETERS = EvParameters(
    site_limit_kw=Fraction(80), base_load_kw=Fraction(0), connector_rating_kw=Fraction(60),
    charger_rating_kw=Fraction(60), enabled_from=time(8, 0), enabled_to=time(16, 0),
)


@dataclass(frozen=True)
class EvForcingRow:
    """One private forcing at a UTC minute boundary (`ev-scenario/1` forcing row)."""

    at: datetime
    kind: str
    connector: str
    value: str


@dataclass(frozen=True)
class EvEvent:
    """A transition the model emitted at boundary `at`: START, END, ABORT, FAULT or CLEAR.

    `session_id` is the scoped token when one is active at the transition, else None.
    """

    at: datetime
    connector: str
    kind: str
    session_id: str | None


@dataclass(frozen=True)
class ConnectorState:
    connector: str
    state: str = "UNPLUGGED"
    session_id: str | None = None
    started: bool = False
    request_kw: Fraction = Fraction(0)
    allocated_kw: Fraction = Fraction(0)
    energy_kwh: Fraction = Fraction(0)
    fault: bool = False
    authorized_at: datetime | None = None

    def check(self) -> None:
        """Every per-connector invariant (Q13, Q14)."""
        if self.connector not in CONNECTORS:
            raise PhysicallyUnacceptable(f"connector {self.connector!r} is not declared")
        if self.state not in CONNECTOR_STATES:
            raise PhysicallyUnacceptable(f"connector state {self.state!r} is not an ev-charger/1 state")
        if self.state in ("PLUGGED", "AUTHORIZING", "CHARGING") and self.session_id is None:
            raise PhysicallyUnacceptable(f"{self.connector} is {self.state} without a valid session")
        if self.state == "UNPLUGGED" and self.session_id is not None:
            raise PhysicallyUnacceptable(f"{self.connector} is UNPLUGGED with a session")
        if self.fault != (self.state == "FAULTED"):
            raise PhysicallyUnacceptable(f"{self.connector} fault latch disagrees with state {self.state}")
        if self.started != (self.state == "CHARGING"):
            raise PhysicallyUnacceptable(f"{self.connector} started flag disagrees with state {self.state}")
        if (self.authorized_at is not None) != (self.state == "AUTHORIZING"):
            raise PhysicallyUnacceptable(f"{self.connector} authorization disagrees with state {self.state}")
        if self.state != "CHARGING" and self.allocated_kw != 0:
            raise PhysicallyUnacceptable(f"{self.connector} allocates power while {self.state}")
        for name in ("request_kw", "allocated_kw", "energy_kwh"):
            if getattr(self, name) < 0:
                raise PhysicallyUnacceptable(f"{self.connector} {name} is negative")


@dataclass(frozen=True)
class EvState:
    minute: datetime
    connectors: tuple[ConnectorState, ...]
    #: Index into CONNECTORS of the connector that receives the next 1 kW quantum.
    pointer: int = 0
    plugs: int = 0
    started_sessions: frozenset[str] = frozenset()
    terminal_sessions: frozenset[str] = frozenset()
    forcing_ordinal: int | None = None

    @classmethod
    def initial(cls, minute: datetime) -> "EvState":
        return cls(minute, tuple(ConnectorState(c) for c in CONNECTORS))

    def connector(self, connector: str) -> ConnectorState:
        return self.connectors[CONNECTOR_RANK[connector]]

    def with_connector(self, value: ConnectorState) -> "EvState":
        items = list(self.connectors)
        items[CONNECTOR_RANK[value.connector]] = value
        return replace(self, connectors=tuple(items))


@dataclass(frozen=True)
class EvMinute:
    """One boundary: its private document, the events emitted at it, and the state after integration."""

    document: dict[str, Any]
    events: tuple[EvEvent, ...]
    after: EvState


class EvChargerPack:
    """`ev-charger/1`: the closed connector/session state machine and shared-cap allocation."""

    def __init__(self, parameters: EvParameters, *, scenario_sha256: str,
                 grid_available: bool = True) -> None:
        self.parameters = parameters
        self.scenario_sha256 = scenario_sha256
        #: Q3: a typed grid-available input retained for future profiles, frozen True for every 05b minute.
        self.grid_available = grid_available

    # --- forcing -------------------------------------------------------------------------------------

    def _apply(self, state: EvState, row: EvForcingRow, events: list[EvEvent]) -> EvState:
        c = state.connector(row.connector)
        kind, value, at = row.kind, row.value, row.at

        def refuse(reason: str) -> PhysicallyUnacceptable:
            return PhysicallyUnacceptable(f"{_instant(at)} {kind} {value} on {c.connector} ({c.state}): {reason}")

        if kind == "PLUG":
            if c.state != "UNPLUGGED":
                raise refuse("only an unplugged connector can be plugged")
            if state.plugs >= len(PLUG_LABELS) or value != PLUG_LABELS[state.plugs]:
                raise refuse("plug labels follow session-1 then session-2 without reuse")
            session = scoped_session_id(self.scenario_sha256, value)
            state = replace(state, plugs=state.plugs + 1)
            return state.with_connector(replace(c, state="PLUGGED", session_id=session, request_kw=Fraction(0)))
        if kind == "AUTHORIZE":
            if value not in ("ACCEPT", "DENY"):
                raise refuse("AUTHORIZE takes ACCEPT or DENY")
            if c.state != "PLUGGED":
                raise refuse("only a plugged, unstarted connector can be authorized")
            if value == "ACCEPT":
                return state.with_connector(replace(c, state="AUTHORIZING", authorized_at=at))
            return state.with_connector(replace(c, request_kw=Fraction(0)))
        if kind == "REQUEST_KW":
            try:
                request = Fraction(value)
            except (ValueError, ZeroDivisionError) as error:
                raise refuse("the request is not a decimal") from error
            if request < 0:
                raise refuse("the request is negative")
            if c.state not in ("PLUGGED", "AUTHORIZING", "CHARGING"):
                raise refuse("a request needs a plugged connector")
            return state.with_connector(replace(c, request_kw=request))
        if value != _FIXED_VALUES.get(kind):
            raise refuse(f"{kind} does not take {value!r}")
        if kind == "FAULT":
            if c.state == "FAULTED":
                return state  # no-op; no duplicate FAULT
            if c.state == "CHARGING":
                session = c.session_id
                assert session is not None
                self._terminate(state, session, refuse)
                events.append(EvEvent(at, c.connector, "FAULT", session))
                events.append(EvEvent(at, c.connector, "ABORT", session))
                state = replace(state, terminal_sessions=state.terminal_sessions | {session})
                return state.with_connector(replace(
                    c, state="FAULTED", session_id=None, started=False, request_kw=Fraction(0),
                    allocated_kw=Fraction(0), fault=True))
            events.append(EvEvent(at, c.connector, "FAULT", c.session_id))
            return state.with_connector(replace(
                c, state="FAULTED", request_kw=Fraction(0), fault=True, authorized_at=None))
        if kind == "CLEAR":
            if c.state != "FAULTED":
                raise refuse("only a faulted connector can be cleared")
            events.append(EvEvent(at, c.connector, "CLEAR", c.session_id))
            next_state = "PLUGGED" if c.session_id is not None else "UNPLUGGED"
            return state.with_connector(replace(c, state=next_state, fault=False, request_kw=Fraction(0)))
        if kind == "UNPLUG":
            if c.state == "FAULTED":
                raise refuse("a faulted connector cannot be unplugged until CLEAR")
            if c.state == "UNPLUGGED":
                return state  # no-op
            if c.state == "CHARGING":
                session = c.session_id
                assert session is not None
                self._terminate(state, session, refuse)
                events.append(EvEvent(at, c.connector, "END", session))
                state = replace(state, terminal_sessions=state.terminal_sessions | {session})
            return state.with_connector(replace(
                c, state="UNPLUGGED", session_id=None, started=False, request_kw=Fraction(0),
                allocated_kw=Fraction(0), authorized_at=None))
        raise refuse("not an ev-charger/1 forcing kind")

    @staticmethod
    def _terminate(state: EvState, session: str, refuse) -> None:
        if session not in state.started_sessions:
            raise refuse("a terminal needs a started session")
        if session in state.terminal_sessions:
            raise refuse("the session already has a terminal")

    # --- allocation ----------------------------------------------------------------------------------

    def _enabled(self, minute: datetime) -> bool:
        return self.parameters.enabled_from <= minute.time() < self.parameters.enabled_to

    def available_kw(self) -> Fraction:
        if not self.grid_available:
            return Fraction(0)
        return max(Fraction(0), self.parameters.site_limit_kw - self.parameters.base_load_kw)

    def _allocate(self, state: EvState) -> EvState:
        p = self.parameters
        caps = {
            c.connector: (min(c.request_kw, p.connector_rating_kw, p.charger_rating_kw)
                          if c.state == "CHARGING" and self._enabled(state.minute) else Fraction(0))
            for c in state.connectors
        }
        allocated = {connector: Fraction(0) for connector in CONNECTORS}
        remaining = self.available_kw()
        pointer = state.pointer
        while remaining > 0 and any(allocated[c] < caps[c] for c in CONNECTORS):
            connector = CONNECTORS[pointer]
            headroom = caps[connector] - allocated[connector]
            if headroom > 0:
                quantum = min(QUANTUM_KW, headroom, remaining)
                allocated[connector] += quantum
                remaining -= quantum
            pointer = (pointer + 1) % len(CONNECTORS)
        for connector in CONNECTORS:
            state = state.with_connector(replace(state.connector(connector), allocated_kw=allocated[connector]))
        return replace(state, pointer=pointer)

    # --- the minute ----------------------------------------------------------------------------------

    def step(self, state: EvState, forcing: tuple[EvForcingRow, ...] = (), *,
             ordinals: tuple[int, ...] = (), transition: bool = True) -> EvMinute:
        """One boundary. `transition=False` is the closing snapshot: no forcing, transition or allocation.

        `ordinals` are the zero-based document indexes of `forcing`, one per row, continuing the prior sequence
        (`state.forcing_ordinal + 1`, or 0 before any row): N8 refuses a missing, short, long, repeated or skipped
        ordinal list rather than silently record a wrong `forcing_ordinal` in the private digest.
        """
        t = state.minute
        events: list[EvEvent] = []
        if not transition:
            if forcing or ordinals:
                raise PhysicallyUnacceptable(f"forcing at the closing boundary {_instant(t)}")
            for c in state.connectors:
                state = state.with_connector(replace(c, allocated_kw=Fraction(0)))
            self._check(state)
            return EvMinute(self._document(state), (), state)
        first = 0 if state.forcing_ordinal is None else state.forcing_ordinal + 1
        if tuple(ordinals) != tuple(range(first, first + len(forcing))):
            raise PhysicallyUnacceptable(
                f"forcing ordinals {list(ordinals)} at {_instant(t)} do not continue the forcing sequence "
                f"from {first} one-for-one with {len(forcing)} row(s)"
            )
        keys = [(f.at, CONNECTOR_RANK.get(f.connector, -1), FORCING_KIND_RANK.get(f.kind, -1)) for f in forcing]
        for f, key in zip(forcing, keys):
            if f.at != t:
                raise PhysicallyUnacceptable(f"forcing at {_instant(f.at)} applied at boundary {_instant(t)}")
            if key[1] < 0 or key[2] < 0:
                raise PhysicallyUnacceptable(f"forcing {f.kind} on {f.connector!r} is not ev-charger/1 forcing")
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise PhysicallyUnacceptable(f"forcing at {_instant(t)} is unordered or repeated")
        # 1. forcing
        for f in forcing:
            state = self._apply(state, f, events)
        if forcing:
            state = replace(state, forcing_ordinal=ordinals[-1])
        # 2. authorization completion
        for c in state.connectors:
            if c.state == "AUTHORIZING" and c.authorized_at is not None and c.authorized_at < t:
                session = c.session_id
                assert session is not None
                if session in state.started_sessions:
                    raise PhysicallyUnacceptable(f"{_instant(t)} {c.connector}: START twice for one session")
                events.append(EvEvent(t, c.connector, "START", session))
                state = replace(state, started_sessions=state.started_sessions | {session})
                state = state.with_connector(replace(c, state="CHARGING", started=True, authorized_at=None))
        # 3. allocation for [t, t+1)
        state = self._allocate(state)
        self._check(state)
        document = self._document(state)
        # 4. exact integration
        before_total = sum((c.energy_kwh for c in state.connectors), Fraction(0))
        draw = sum((c.allocated_kw for c in state.connectors), Fraction(0))
        after = replace(state, minute=t + STEP)
        for c in state.connectors:
            after = after.with_connector(replace(c, energy_kwh=c.energy_kwh + c.allocated_kw / MINUTES_PER_HOUR))
        after_total = sum((c.energy_kwh for c in after.connectors), Fraction(0))
        if after_total - before_total != draw / MINUTES_PER_HOUR:
            raise PhysicallyUnacceptable(f"{_instant(t)}: energy residual is not zero")
        return EvMinute(document, tuple(events), after)

    def _check(self, state: EvState) -> None:
        available = self.available_kw()
        total = Fraction(0)
        p = self.parameters
        for c in state.connectors:
            c.check()
            if c.allocated_kw > min(c.request_kw, p.connector_rating_kw, p.charger_rating_kw):
                raise PhysicallyUnacceptable(f"{c.connector} allocation exceeds its request or rating")
            total += c.allocated_kw
        if total > available:
            raise PhysicallyUnacceptable(f"allocation {total} kW exceeds available {available} kW")
        if total + p.base_load_kw > p.site_limit_kw and total > 0:
            raise PhysicallyUnacceptable("Site import exceeds the Site limit")
        sessions = [c.session_id for c in state.connectors if c.session_id is not None]
        if len(sessions) != len(set(sessions)):
            raise PhysicallyUnacceptable("two connectors hold one session")

    def _document(self, state: EvState) -> dict[str, Any]:
        draw = sum((c.allocated_kw for c in state.connectors), Fraction(0))
        return {
            "boundary": _instant(state.minute),
            "connectors": [
                {
                    "connector": c.connector, "state": c.state, "session_id": c.session_id,
                    "requested_kw": exact_text(c.request_kw), "allocated_kw": exact_text(c.allocated_kw),
                    "energy_kwh": exact_text(c.energy_kwh), "fault": c.fault,
                }
                for c in state.connectors
            ],
            "site_available_kw": exact_text(self.available_kw()),
            "site_import_kw": exact_text(self.parameters.base_load_kw + draw),
            "forcing_ordinal": state.forcing_ordinal,
        }


@dataclass(frozen=True)
class EvRun:
    """A whole window: one private document per boundary (61 for one hour), the events and the final state."""

    minutes: tuple[EvMinute, ...]
    events: tuple[EvEvent, ...] = field(default=())

    @property
    def documents(self) -> tuple[dict[str, Any], ...]:
        return tuple(m.document for m in self.minutes)

    @property
    def final(self) -> EvState:
        return self.minutes[-1].after

    def content_digest(self) -> str:
        """SHA-256 of canonical JSON `["ev-charger/1", ordered private boundary documents]`."""
        return _sha256(["ev-charger/1", list(self.documents)])


def run_window(pack: EvChargerPack, *, start: datetime, end: datetime,
               forcing: tuple[EvForcingRow, ...]) -> EvRun:
    """Step every minute in `[start, end)` and snapshot the closing boundary at `end`."""
    if not start < end or (end - start) % STEP:
        raise PhysicallyUnacceptable("the window is not a positive whole number of minutes")
    by_minute: dict[datetime, list[tuple[int, EvForcingRow]]] = {}
    previous: datetime | None = None
    for ordinal, row in enumerate(forcing):
        if not start <= row.at < end:
            raise PhysicallyUnacceptable(f"forcing at {_instant(row.at)} is outside the run window")
        if row.at.second or row.at.microsecond:
            raise PhysicallyUnacceptable(f"forcing at {_instant(row.at)} is not on a minute boundary")
        if previous is not None and row.at < previous:
            raise PhysicallyUnacceptable("forcing time is not monotone")
        previous = row.at
        by_minute.setdefault(row.at, []).append((ordinal, row))
    state = EvState.initial(start)
    minutes: list[EvMinute] = []
    t = start
    while t < end:
        rows = by_minute.get(t, [])
        minute = pack.step(state, tuple(r for _, r in rows), ordinals=tuple(o for o, _ in rows))
        minutes.append(minute)
        state = minute.after
        t += STEP
    minutes.append(pack.step(state, transition=False))
    events = tuple(e for m in minutes for e in m.events)
    return EvRun(tuple(minutes), events)


__all__ = [
    "CONNECTORS", "CONNECTOR_STATES", "DEFAULT_PARAMETERS", "EVENT_KINDS", "ConnectorState", "EvChargerPack",
    "EvEvent", "EvForcingRow", "EvMinute", "EvParameters", "EvRun", "EvState", "MODEL_PROFILE",
    "PhysicallyUnacceptable", "exact_text", "run_window", "scoped_session_id",
]
