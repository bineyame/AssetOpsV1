"""CH-1b: the event register and its resolution (design §5.2 A0, AG-7; build sheet CH-1b §2 and §3).

The register (``config/chain/event-register-v1.yaml``, reviewed as code) maps each outbox event type to the
Site-local days and the measures it dirties. Resolution happens here, never in SQL: a span is converted to
Site-local days through ``site.timezone``, and a span covering several days marks each day. No outcome id appears
in the register, the events or the resolution (OL-1, plan §2.4): the register names measures only.

``consume`` (one consumer, one Site, bounded) reads unprocessed outbox events through an ``EventPort`` and, for the
``snapshots`` consumer, marks the resolved (day, measure) pairs dirty and records the consumption, one page per
transaction with the page's marks coalesced (ruling CH1b-R2). The ``threads`` consumer is handed the events
(``on_event``) and records each consumption after it, one event per transaction.
"""

from __future__ import annotations

import re
import time
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
#: ANY-1 AR-1: the native grains of a stored read-period kind (`site_period_read`); `local_day` is the register's day.
KIND_GRAINS = ("hour", "s3_day", "local_day")
KIND_SITE_TYPES = ("MINIGRID", "COLDCHAIN", "EV_CHARGING")
KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,40}\.[a-z][a-z0-9_]{1,40}$")


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
class KindRule:
    """ANY-1 AR-1: a stored read-period kind, dirtied like a measure (its `inputs` use the measure input keys)."""
    kind: str
    grain: str
    site_types: frozenset[str]
    inputs: InputRule


@dataclass(frozen=True)
class EventRegister:
    register_version: int
    events: Mapping[str, EventRule]
    inputs: Mapping[str, InputRule]
    kinds: Mapping[str, KindRule] = field(default_factory=dict)

    def rule(self, type_: str, schema_version: int) -> EventRule | None:
        return self.events.get(f"{type_}@{schema_version}")

    def kinds_for(self, site_type: str) -> list[str]:
        return sorted(k for k, r in self.kinds.items() if site_type in r.site_types)

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
        out_inputs[str(measure)] = _input_rule(spec, f"{source}: inputs.{measure}")
    kinds = payload.get("kinds") or {}
    if not isinstance(kinds, dict):
        raise RegisterError(f"{source}: kinds must be a mapping")
    out_kinds: dict[str, KindRule] = {}
    for kind, spec in kinds.items():
        where = f"{source}: kinds.{kind}"
        if not KIND_PATTERN.match(str(kind)):
            raise RegisterError(f"{where}: a kind is '<area>.<name>' in lower case (e.g. mini_depth.renewable)")
        if str(kind) in out_inputs:
            raise RegisterError(f"{where}: a kind and a measure share a name")
        if not isinstance(spec, dict) or set(spec) - {"grain", "site_types", "inputs"}:
            raise RegisterError(f"{where}: keys must be among ('grain', 'site_types', 'inputs')")
        if spec.get("grain") not in KIND_GRAINS:
            raise RegisterError(f"{where}: grain must be in {KIND_GRAINS}")
        site_types = _strings(spec.get("site_types"), where + ".site_types")
        if not site_types or site_types - set(KIND_SITE_TYPES):
            raise RegisterError(f"{where}: site_types must name some of {KIND_SITE_TYPES}")
        rule = _input_rule(spec.get("inputs") or {}, where + ".inputs")
        if rule == InputRule():
            raise RegisterError(f"{where}: a kind declares what dirties it (inputs)")
        out_kinds[str(kind)] = KindRule(str(kind), spec["grain"], site_types, rule)
    return EventRegister(1, out_events, out_inputs, out_kinds)


def _input_rule(spec: Any, where: str) -> InputRule:
    if not isinstance(spec, dict) or set(spec) - set(INPUT_KEYS):
        raise RegisterError(f"{where} keys must be among {INPUT_KEYS}")
    return InputRule(
        roles=_strings(spec.get("roles"), where + ".roles"),
        analytics=_strings(spec.get("analytics"), where + ".analytics"),
        mini_depth=_strings(spec.get("mini_depth"), where + ".mini_depth"),
        job_domains=_strings(spec.get("job_domains"), where + ".job_domains"),
        assumption_keys=_strings(spec.get("assumption_keys"), where + ".assumption_keys"),
        foundation=bool(spec.get("foundation", False)))


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


def _hit(measures_rule: str | None, inp: InputRule, subject: Mapping[str, Any]) -> bool:
    if measures_rule == "by_role":
        return bool(inp.roles & set(subject.get("roles") or ()))
    if measures_rule == "by_analytic":
        return (bool(inp.analytics & set(subject.get("analytic_ids") or ()))
                or (subject.get("domain") is not None and subject.get("domain") in inp.mini_depth))
    if measures_rule == "by_job_domain":
        return subject.get("domain") in inp.job_domains
    if measures_rule == "by_assumption_key":
        return subject.get("key") in inp.assumption_keys
    return False


def _measures(register: EventRegister, rule: EventRule, subject: Mapping[str, Any], site_type: str) -> list[str]:
    """The measures, then the stored read-period kinds (AR-1), the event dirties for this Site type."""
    keys = [m.key for m in measures_for(site_type)]
    kinds = register.kinds_for(site_type)
    if rule.measures == "all_of_site":
        return keys + kinds
    picked = [k for k in keys if _hit(rule.measures, register.inputs.get(k, InputRule()), subject)]
    return picked + [k for k in kinds if _hit(rule.measures, register.kinds[k].inputs, subject)]


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
    """The (Site-local day, measure or read-period kind) pairs an event dirties; empty for a `days: none` event or an
    unknown type. A kind's pairs go through the same `snapshot_dirty` queue (its `measure` column holds the kind)."""
    rule = register.rule(event.type, event.schema_version)
    if rule is None or "snapshots" not in rule.consumers:
        return []
    measures = _measures(register, rule, event.subject, site_type)
    if not measures:
        return []
    s3 = [m for m in measures if m in register.kinds and register.kinds[m].grain == "s3_day"]
    out = [(d, m) for d in _days(rule, event.subject, tz, today) for m in measures if m not in s3]
    if s3:  # ANY-2 AR-3: an s3_day kind's day is the UTC day of its S3 window, never the Site-local day
        out += [(d, m) for d in _s3_days(rule, event.subject, today) for m in s3]
    return out


#: ANY-2 AR-3: the S3 evidence bracket (`analytics/assessment_inputs.py` BRACKET): a reading this close to a UTC day's
#: window is in that window's evidence query, so it dirties that day too.
S3_BRACKET = timedelta(hours=6)


def _s3_days(rule: EventRule, subject: Mapping[str, Any], today: date | None) -> list[date]:
    """The UTC days whose S3 dispatch window (with its bracket) the event's spans touch. `today` is the Site-local
    day; a UTC day can be one later, so the clamp is `today + 1` (over-dirtying a day only rebuilds it)."""
    clamp = None if today is None else today + timedelta(days=1)

    def utc(lo: Any, hi: Any) -> list[date]:
        a = _instant(lo)
        if a is None:
            return []
        b = _instant(hi)
        if b is None and clamp is None:
            b = a
        return local_days(a - S3_BRACKET, None if b is None else max(b, a) + S3_BRACKET, "UTC", clamp)

    if rule.days == "none":
        return []
    if rule.days == "span_local":
        spans = [subject.get("span") or [None, None]]
    elif rule.days == "windows_local":
        spans = list(subject.get("windows") or ())
    elif rule.days == "window_local":
        spans = [subject.get("window") or [None, None]]
    elif rule.days == "valid_local":
        spans = [subject.get("valid") or [None, None]]
    elif rule.days == "from_valid_local_to_today":
        spans = [[subject.get("valid_from"), None]]
    else:
        raise RegisterError(f"unknown day rule {rule.days!r}")
    return sorted({d for w in spans for d in utc(w[0], w[1])})


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
        record ``(consumer, event_id)`` in ``event_consumption``. The per-event form (the threads consumer)."""

    def mark_and_consume_page(self, consumer: str, events: Sequence[Event], marks: Sequence[Mark]) -> None:
        """In ONE transaction for a whole page (ruling CH1b-R2 note 3): upsert every coalesced mark (distinct on
        (tenant, Site, day, measure)), then record ``(consumer, event_id)`` for every event of the page."""

    def site_today(self, tenant_id: UUID, site_id: UUID, tz: str) -> date: ...


@dataclass(frozen=True)
class Mark:
    """One coalesced dirty mark of a page; ``first_event_id`` is the page's earliest event (read order) naming it."""
    tenant_id: UUID
    site_id: UUID
    local_day: date
    measure: str
    first_event_id: UUID


def coalesce(page: Sequence[tuple[Event, Sequence[tuple[date, str]]]]) -> list[Mark]:
    """A page's marks, one per (tenant, Site, day, measure), each keeping the first event of the page that named it
    (the page is in read order). Deduplicated before the upsert, which cannot affect one row twice."""
    first: dict[tuple[UUID, UUID, date, str], UUID] = {}
    for ev, marks in page:
        for day, measure in marks:
            first.setdefault((ev.tenant_id, ev.site_id, day, measure), ev.event_id)
    ordered = sorted(first.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), kv[0][2], kv[0][3]))
    return [Mark(t, s, d, m, e) for (t, s, d, m), e in ordered]


@dataclass
class ConsumeReport:
    consumer: str
    consumed: int = 0
    marked: int = 0
    pages: int = 0
    stopped: str | None = None  # "deadline" | None (the queue was emptied)
    ms: float = 0.0
    select_ms: list[float] = field(default_factory=list)
    by_type: dict[str, int] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return {"consumer": self.consumer, "consumed": self.consumed, "marked": self.marked, "pages": self.pages,
                "stopped": self.stopped, "ms": round(self.ms, 1),
                "select_ms": [round(x, 1) for x in self.select_ms],
                "by_type": dict(sorted(self.by_type.items()))}


def _count(report: ConsumeReport, ev: Event) -> None:
    report.consumed += 1
    report.by_type[ev.key] = report.by_type.get(ev.key, 0) + 1


def consume(port: EventPort, register: EventRegister, consumer: str, tenant_id: UUID, site_id: UUID,
            site: SiteInfo, limit: int, *, on_event: Callable[[Event], None] | None = None,
            deadline: Callable[[], bool] | None = None, today: date | None = None) -> ConsumeReport:
    """Consume this Site's events for `consumer`, oldest first, in pages of `limit`, until the queue is empty or
    `deadline` passes (ruling DD0-R: the bound limits time, not rows; the rest stays queued, never a failure).

    - ``snapshots``: each page's marks are coalesced and written with every consumption row of the page in ONE
      transaction (``mark_and_consume_page``). ``today`` (read once per stage run, ruling CH1b-R2 note 1) clamps
      every page; when not given it is read here once, on the first non-empty page.
    - ``threads``/``lifecycle``: one event per transaction. `on_event` (the threads consumer) runs before the
      consumption is recorded, so a failure leaves only that event unconsumed and it is retried."""
    if consumer not in CONSUMERS:
        raise ValueError(f"unknown consumer {consumer!r}")
    report = ConsumeReport(consumer)
    names = sorted({k.partition("@")[0] for k in register.consumes(consumer)})
    started = time.perf_counter()
    try:
        while True:
            if deadline is not None and deadline():
                report.stopped = "deadline"
                break
            t0 = time.perf_counter()
            events = port.unconsumed(consumer, tenant_id, site_id, names, limit)
            report.select_ms.append((time.perf_counter() - t0) * 1000)
            if not events:
                break
            if consumer == "snapshots":
                if today is None:
                    today = port.site_today(tenant_id, site_id, site.timezone)
                marks = coalesce([(ev, resolve(register, ev, site_type=site.site_type, tz=site.timezone, today=today))
                                  for ev in events])
                port.mark_and_consume_page(consumer, events, marks)
                report.marked += len(marks)
                for ev in events:
                    _count(report, ev)
            else:
                for ev in events:
                    if deadline is not None and deadline():
                        report.stopped = "deadline"
                        return report
                    rule = register.rule(ev.type, ev.schema_version)
                    if on_event is not None and rule is not None and consumer in rule.consumers:
                        on_event(ev)
                    port.mark_and_consume(consumer, ev, [])
                    _count(report, ev)
            report.pages += 1
            if len(events) < limit:
                break
    finally:
        report.ms = (time.perf_counter() - started) * 1000
    return report


def consume_exactly(port: EventPort, consumer: str, events: Sequence[Event]) -> ConsumeReport:
    """Record exactly these events as consumed by `consumer` in one transaction, with no marks. The lifecycle
    consumer reads its unconsumed ids BEFORE ``run_lifecycle`` and records only those after it (review L2), so an
    event committed while the run read the state stays unconsumed for the next run."""
    report = ConsumeReport(consumer)
    if events:
        port.mark_and_consume_page(consumer, events, [])
        report.pages = 1
    for ev in events:
        _count(report, ev)
    return report


__all__ = ["CONSUMERS", "ConsumeReport", "Event", "EventPort", "EventRegister", "EventRule", "InputRule", "KindRule", "Mark",
           "RegisterError", "SiteInfo", "coalesce", "consume", "consume_exactly", "local_days", "parse_register",
           "resolve"]
