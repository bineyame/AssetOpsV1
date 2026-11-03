"""CH-1b: the event register and its resolution (design §5.2 A0, AG-7; build sheet CH-1b §2 and §3).

The register (``config/chain/event-register-v1.yaml``, reviewed as code) maps each outbox event type to the
Site-local days and the measures it dirties. Resolution happens here, never in SQL: a span is converted to
Site-local days through ``site.timezone``, and a span covering several days marks each day. No outcome id appears
in the register, the events or the resolution (OL-1, plan §2.4): the register names measures only.

``consume`` (one consumer, one Site, bounded) reads unprocessed outbox events through an ``EventPort`` and, for the
``snapshots`` consumer, marks the resolved (day, measure) pairs dirty and records the consumption, one event per
transaction. The ``threads`` consumer is handed the events (``on_event``) and records the consumption after it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Protocol, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from .measures import measures_for

CONSUMERS = ("snapshots", "threads", "lifecycle")
DAY_RULES = ("span_local", "windows_local", "window_local", "valid_local", "from_valid_local_to_today", "none")
MEASURE_RULES = ("by_role", "by_analytic", "by_job_domain", "by_assumption_key", "all_of_site")
INPUT_KEYS = ("roles", "analytics", "mini_depth", "job_domains", "assumption_keys", "foundation")


class RegisterError(ValueError):
    """The declared event register does not match its schema."""


@dataclass(frozen=True)
class EventRule:
    type: str  # e.g. "reading.accepted@1"
    days: str
    measures: str | None
    consumers: tuple[str, ...]


@dataclass(frozen=True)
class InputRule:
    roles: frozenset[str] = frozenset()
    analytics: frozenset[str] = frozenset()
    mini_depth: frozenset[str] = frozenset()
    job_domains: frozenset[str] = frozenset()
    assumption_keys: frozenset[str] = frozenset()
    foundation: bool = False


@dataclass(frozen=True)
class EventRegister:
    register_version: int
    events: Mapping[str, EventRule]
    inputs: Mapping[str, InputRule]

    def rule(self, type_: str, schema_version: int) -> EventRule | None:
        return self.events.get(f"{type_}@{schema_version}")

    def consumes(self, consumer: str) -> list[str]:
        """The `type@version` keys a consumer reads."""
        return sorted(k for k, r in self.events.items() if consumer in r.consumers)


def _strings(value: Any, where: str) -> frozenset[str]:
    if value is None:
        return frozenset()
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        raise RegisterError(f"{where}: must be a list of names")
    return frozenset(value)


def parse_register(payload: Any, source: str = "event register") -> EventRegister:
    if not isinstance(payload, dict) or payload.get("register_version") != 1:
        raise RegisterError(f"{source}: register_version must be 1")
    events, inputs = payload.get("events"), payload.get("inputs")
    if not isinstance(events, dict) or not isinstance(inputs, dict):
        raise RegisterError(f"{source}: events and inputs must be mappings")
    out_events: dict[str, EventRule] = {}
    for key, spec in events.items():
        name, _, version = str(key).partition("@")
        if not version.isdigit() or int(version) < 1 or "." not in name:
            raise RegisterError(f"{source}: event {key!r} must be '<area>.<name>@<version>'")
        if not isinstance(spec, dict) or spec.get("days") not in DAY_RULES:
            raise RegisterError(f"{source}: event {key!r} needs days in {DAY_RULES}")
        measures = spec.get("measures")
        if spec["days"] == "none":
            if measures is not None:
                raise RegisterError(f"{source}: event {key!r} has days none and so names no measures")
        elif measures not in MEASURE_RULES:
            raise RegisterError(f"{source}: event {key!r} needs measures in {MEASURE_RULES}")
        consumers = spec.get("consumer", "snapshots" if spec["days"] != "none" else [])
        consumers = tuple([consumers] if isinstance(consumers, str) else consumers)
        if any(c not in CONSUMERS for c in consumers):
            raise RegisterError(f"{source}: event {key!r} names an unknown consumer")
        out_events[str(key)] = EventRule(str(key), spec["days"], measures, consumers)
    out_inputs: dict[str, InputRule] = {}
    for measure, spec in inputs.items():
        if not isinstance(spec, dict) or set(spec) - set(INPUT_KEYS):
            raise RegisterError(f"{source}: inputs.{measure} keys must be among {INPUT_KEYS}")
        where = f"{source}: inputs.{measure}"
        out_inputs[str(measure)] = InputRule(
            roles=_strings(spec.get("roles"), where + ".roles"),
            analytics=_strings(spec.get("analytics"), where + ".analytics"),
            mini_depth=_strings(spec.get("mini_depth"), where + ".mini_depth"),
            job_domains=_strings(spec.get("job_domains"), where + ".job_domains"),
            assumption_keys=_strings(spec.get("assumption_keys"), where + ".assumption_keys"),
            foundation=bool(spec.get("foundation", False)))
    return EventRegister(1, out_events, out_inputs)


# --- resolution -------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Event:
    event_id: UUID
    type: str
    schema_version: int
    occurred_at: datetime
    recorded_at: datetime
    source: str
    tenant_id: UUID
    site_id: UUID | None
    subject: Mapping[str, Any]
    payload: Mapping[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.type}@{self.schema_version}"


def _instant(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    if len(text) == 10:  # a bare date: its UTC midnight
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def local_days(start: Any, end: Any, tz: str, today: date | None = None) -> list[date]:
    """Every Site-local day the half-open span ``[start, end)`` touches (an empty or point span: its start day).
    An open end (None) runs to ``today``; every day is clamped to ``today`` when given."""
    zone = ZoneInfo(tz)
    lo = _instant(start)
    if lo is None:
        return []
    hi = _instant(end)
    first = lo.astimezone(zone).date()
    if hi is None:
        if today is None:
            return [first]
        last = today
    elif hi <= lo:
        last = first
    else:
        last = (hi - timedelta(microseconds=1)).astimezone(zone).date()
    if today is not None:
        last = min(last, today)
    out, day = [], first
    while day <= last:
        out.append(day)
        day += timedelta(days=1)
    return out


def _measures(register: EventRegister, rule: EventRule, subject: Mapping[str, Any], site_type: str) -> list[str]:
    keys = [m.key for m in measures_for(site_type)]
    if rule.measures == "all_of_site":
        return keys
    picked = []
    for key in keys:
        inp = register.inputs.get(key, InputRule())
        if rule.measures == "by_role":
            hit = bool(inp.roles & set(subject.get("roles") or ()))
        elif rule.measures == "by_analytic":
            hit = (bool(inp.analytics & set(subject.get("analytic_ids") or ()))
                   or (subject.get("domain") is not None and subject.get("domain") in inp.mini_depth))
        elif rule.measures == "by_job_domain":
            hit = subject.get("domain") in inp.job_domains
        elif rule.measures == "by_assumption_key":
            hit = subject.get("key") in inp.assumption_keys
        else:
            hit = False
        if hit:
            picked.append(key)
    return picked


def _days(rule: EventRule, subject: Mapping[str, Any], tz: str, today: date | None) -> list[date]:
    if rule.days == "none":
        return []
    if rule.days == "span_local":
        span = subject.get("span") or [None, None]
        return local_days(span[0], span[1], tz, today)
    if rule.days == "windows_local":
        return sorted({d for w in subject.get("windows") or () for d in local_days(w[0], w[1], tz, today)})
    if rule.days == "window_local":
        w = subject.get("window") or [None, None]
        return local_days(w[0], w[1], tz, today)
    if rule.days == "valid_local":
        v = subject.get("valid") or [None, None]
        return local_days(v[0], v[1], tz, today)
    if rule.days == "from_valid_local_to_today":
        return local_days(subject.get("valid_from"), None, tz, today)
    raise RegisterError(f"unknown day rule {rule.days!r}")


def resolve(register: EventRegister, event: Event, *, site_type: str, tz: str,
            today: date | None) -> list[tuple[date, str]]:
    """The (Site-local day, measure) pairs an event dirties; empty for a `days: none` event or an unknown type."""
    rule = register.rule(event.type, event.schema_version)
    if rule is None or "snapshots" not in rule.consumers:
        return []
    measures = _measures(register, rule, event.subject, site_type)
    if not measures:
        return []
    return [(d, m) for d in _days(rule, event.subject, tz, today) for m in measures]


# --- the port and the consumer ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class SiteInfo:
    site_type: str
    timezone: str


class EventPort(Protocol):
    def unconsumed(self, consumer: str, tenant_id: UUID, site_id: UUID, types: Sequence[str],
                   limit: int) -> list[Event]: ...

    def mark_and_consume(self, consumer: str, event: Event, marks: Sequence[tuple[date, str]]) -> None:
        """In ONE transaction: upsert every mark into ``snapshot_dirty`` (a re-mark refreshes ``marked_at``), then
        record ``(consumer, event_id)`` in ``event_consumption``."""

    def site_today(self, tenant_id: UUID, site_id: UUID, tz: str) -> date: ...


@dataclass
class ConsumeReport:
    consumer: str
    consumed: int = 0
    marked: int = 0
    by_type: dict[str, int] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return {"consumer": self.consumer, "consumed": self.consumed, "marked": self.marked,
                "by_type": dict(sorted(self.by_type.items()))}


def consume(port: EventPort, register: EventRegister, consumer: str, tenant_id: UUID, site_id: UUID,
            site: SiteInfo, limit: int, *, on_event: Callable[[Event], None] | None = None,
            deadline: Callable[[], bool] | None = None) -> ConsumeReport:
    """Consume up to `limit` of this Site's events for `consumer`, oldest first. `on_event` (the threads consumer)
    runs before the consumption is recorded, so a failure leaves the event unconsumed and it is retried."""
    if consumer not in CONSUMERS:
        raise ValueError(f"unknown consumer {consumer!r}")
    report = ConsumeReport(consumer)
    names = sorted({k.partition("@")[0] for k in register.consumes(consumer)})
    events = port.unconsumed(consumer, tenant_id, site_id, names, limit)
    today = port.site_today(tenant_id, site_id, site.timezone) if events else None
    for ev in events:
        if deadline is not None and deadline():
            break
        rule = register.rule(ev.type, ev.schema_version)
        marks: list[tuple[date, str]] = []
        if consumer == "snapshots" and rule is not None:
            marks = resolve(register, ev, site_type=site.site_type, tz=site.timezone, today=today)
        elif on_event is not None and rule is not None and consumer in rule.consumers:
            on_event(ev)
        port.mark_and_consume(consumer, ev, marks)
        report.consumed += 1
        report.marked += len(marks)
        report.by_type[ev.key] = report.by_type.get(ev.key, 0) + 1
    return report


__all__ = ["CONSUMERS", "ConsumeReport", "Event", "EventPort", "EventRegister", "EventRule", "InputRule",
           "RegisterError", "SiteInfo", "consume", "local_days", "parse_register", "resolve"]

