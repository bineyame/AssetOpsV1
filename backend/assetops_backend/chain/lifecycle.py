"""CH-3 thread lifecycle (design §4.4, §5.2 A5; build sheet CH-3 §1-§3): the pure state machine, segments and the
read-time thread view. No database driver here.

- `plan_lifecycle` turns a thread's stored events plus its causes into the events to append. A cause that is not
  valid from the current state is skipped and reported, never written and never raised; later causes still apply.
  A cause already stored (`(cause_kind, cause_id)`, M/0042 UNIQUE) is not planned again, so a rerun writes nothing.
- Segments are split at each OPEN, RECURRED or REOPENED event and assigned by STORY time (ruling CH3-R): an
  occurrence by its own start event, else by the segment current on its episode-start day; an Action by the later of
  its origin occurrence's segment and the segment current on its ACCEPTED day. `joined_at` and `linked_at` are never
  read (they are backfill times; DS-R1 item 4).
- `state_on` is the thread state on a Site-local day as of a `known_at` (events with `effective_day <= day` and
  `recorded_at <= known_at`).

OL-1: the policy names measures per mechanism, never outcomes; which outcomes a Finding moves stays in
`outcomes/outcome_map.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from assetops_backend.chain.policy import ChainConfigError

STARTS = ("OPEN", "RECURRED", "REOPENED")
APPLIED_OR_LATER = ("CHANGE_APPLIED", "RESOLVED_MONITORING", "CLOSED")
VERIFIED_STATES = ("RESOLVED_MONITORING", "CLOSED")
ATTENTION_STATES = ("OPEN", "RECURRED", "REOPENED")

# Causes (build sheet §2).
ACTION_ACCEPTED = "ACTION_ACCEPTED"
ACTION_APPLIED = "ACTION_APPLIED"
VERIFIED = "VERIFIED"
INEFFECTIVE = "INEFFECTIVE"
INCONCLUSIVE_EXPIRED = "INCONCLUSIVE_EXPIRED"
RESOLUTION_WITHDRAWN = "RESOLUTION_WITHDRAWN"
CLEAN_DAYS = "CLEAN_DAYS"
OCCURRENCE = "OCCURRENCE"
SUPPORT_LOST = "SUPPORT_LOST"

#: (from_state, cause) -> to_state; design §4.4. `None` is a thread with no event yet.
TRANSITIONS: dict[tuple[str | None, str], str] = {
    **{(s, ACTION_ACCEPTED): "ACTION_IN_HAND" for s in (None, "OPEN", "REOPENED", "RECURRED")},
    ("ACTION_IN_HAND", ACTION_APPLIED): "CHANGE_APPLIED",
    ("CHANGE_APPLIED", VERIFIED): "RESOLVED_MONITORING",
    ("CHANGE_APPLIED", INEFFECTIVE): "REOPENED",
    ("CHANGE_APPLIED", INCONCLUSIVE_EXPIRED): "REOPENED",
    ("RESOLVED_MONITORING", RESOLUTION_WITHDRAWN): "CHANGE_APPLIED",
    ("RESOLVED_MONITORING", CLEAN_DAYS): "CLOSED",
    ("RESOLVED_MONITORING", OCCURRENCE): "RECURRED",
    ("CLOSED", OCCURRENCE): "RECURRED",
    ("OPEN", SUPPORT_LOST): "WITHDRAWN",
}
#: Causes that come from an Action: they apply only when the Action is linked and in the thread's current segment.
ACTION_CAUSES = (ACTION_ACCEPTED, ACTION_APPLIED, VERIFIED, INEFFECTIVE, INCONCLUSIVE_EXPIRED, RESOLUTION_WITHDRAWN)


@dataclass(frozen=True)
class LifecyclePolicy:
    policy_version: str
    close_default: int
    close_by_site_type: Mapping[str, int]
    inconclusive_expiry_days: int
    clean_day_measures: Mapping[str, tuple[str, ...]]

    def close_after(self, site_type: str | None = None) -> int:
        return int(self.close_by_site_type.get(site_type or "", self.close_default))

    def measures_for(self, mechanism: str) -> tuple[str, ...]:
        return tuple(self.clean_day_measures.get(mechanism, ()))


def _positive_int(value: Any, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ChainConfigError(f"{where} must be a positive integer")
    return value


def parse_thread_lifecycle(payload: Mapping[str, Any], source: str = "thread-lifecycle") -> LifecyclePolicy:
    """Validates `config/chain/thread-lifecycle-v1.json`; any other shape raises ChainConfigError."""
    if payload.get("schema") != "thread-lifecycle" or payload.get("version") != 1:
        raise ChainConfigError(f"{source}: schema must be thread-lifecycle version 1")
    pv = payload.get("policy_version")
    if not isinstance(pv, str) or not pv:
        raise ChainConfigError(f"{source}: policy_version is required")
    close = payload.get("close_after_clean_complete_days")
    if not isinstance(close, dict) or not isinstance(close.get("by_site_type", {}), dict):
        raise ChainConfigError(f"{source}: close_after_clean_complete_days must be an object")
    default = _positive_int(close.get("default"), f"{source}: close_after_clean_complete_days.default")
    by_type = {str(k): _positive_int(v, f"{source}: by_site_type.{k}") for k, v in close.get("by_site_type", {}).items()}
    expiry = _positive_int(payload.get("inconclusive_expiry_days"), f"{source}: inconclusive_expiry_days")
    measures = payload.get("clean_day_measures")
    if not isinstance(measures, dict) or not measures:
        raise ChainConfigError(f"{source}: clean_day_measures must be a non-empty object")
    parsed: dict[str, tuple[str, ...]] = {}
    for mechanism, names in measures.items():
        if not isinstance(names, list) or not names or not all(isinstance(n, str) and n for n in names):
            raise ChainConfigError(f"{source}: clean_day_measures.{mechanism} must list measure names")
        parsed[str(mechanism)] = tuple(names)
    return LifecyclePolicy(pv, default, by_type, expiry, parsed)


@dataclass(frozen=True)
class Event:
    seq: int
    state: str
    cause_kind: str
    cause_id: str
    effective_day: date
    recorded_at: datetime | None = None   # None for a planned event (the database stamps it)


@dataclass(frozen=True)
class Cause:
    cause: str                 # one of the causes above
    cause_kind: str            # the stored cause_kind (M/0042 CHECK)
    cause_id: str
    effective_day: date
    recorded_at: datetime
    action_id: str | None = None


@dataclass(frozen=True)
class Occurrence:
    source_id: str
    start_day: date | None     # Site-local day of episode_start (story time); None without one


def local_day(at: datetime, site_tz: str) -> date:
    return at.astimezone(ZoneInfo(site_tz)).date()


def visible(events: Iterable[Event], known_at: datetime | None) -> list[Event]:
    """The events recorded by `known_at` (all of them without one), in seq order."""
    return sorted((e for e in events if known_at is None or e.recorded_at is None or e.recorded_at <= known_at),
                  key=lambda e: e.seq)


def segment_of_event(events: Sequence[Event], seq: int) -> int:
    return max(1, sum(1 for e in events if e.state in STARTS and e.seq <= seq))


def segment_on(events: Sequence[Event], day: date | None) -> int:
    """The segment current on a story day: the number of start events effective on or before it (at least 1)."""
    if day is None:
        return max(1, sum(1 for e in events if e.state in STARTS))
    return max(1, sum(1 for e in events if e.state in STARTS and e.effective_day <= day))


def occurrence_segment(events: Sequence[Event], occ: Occurrence) -> int:
    own = [e for e in events if e.cause_kind == "OCCURRENCE" and e.cause_id == occ.source_id and e.state in STARTS]
    if own:
        return segment_of_event(events, own[0].seq)
    return segment_on(events, occ.start_day)


def action_segment(events: Sequence[Event], origin: Occurrence | None, accepted_day: date | None) -> int:
    origin_seg = occurrence_segment(events, origin) if origin is not None else 1
    if accepted_day is None:
        return origin_seg
    return max(origin_seg, segment_on(events, accepted_day))


def state_on(events: Sequence[Event], day: date, segment: int | None = None) -> tuple[str | None, date | None]:
    """(state, effective_day) of the last event effective on or before `day`, within `segment` when given."""
    last: Event | None = None
    for e in sorted(events, key=lambda x: x.seq):
        if e.effective_day > day:
            continue
        if segment is not None and segment_of_event(events, e.seq) != segment:
            continue
        last = e
    return (None, None) if last is None else (last.state, last.effective_day)


@dataclass
class LifecyclePlan:
    events: list[Event] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)


def plan_lifecycle(thread_id: str, events: Sequence[Event], occurrences: Sequence[Occurrence],
                   actions: Mapping[str, str], causes: Sequence[Cause], *, close_after: int,
                   clean_days: Iterable[date] = ()) -> LifecyclePlan:
    """The events to append to one thread (build sheet §2 rules).

    `actions` maps each Action linked to the thread to its origin Finding id. `clean_days` are the Site-local days on
    which every clean-day measure of the thread's subject is COMPLETE and no occurrence started; the Nth such day
    after the RESOLVED_MONITORING day closes the thread."""
    evs = sorted(events, key=lambda e: e.seq)
    done = {(e.cause_kind, e.cause_id) for e in evs}
    occ_by_source = {o.source_id: o for o in occurrences}
    accepted_day = {c.action_id: c.effective_day for c in causes if c.cause == ACTION_ACCEPTED and c.action_id}
    clean = sorted(set(clean_days))
    plan = LifecyclePlan()

    def head() -> Event | None:
        return evs[-1] if evs else None

    def add(state: str, cause_kind: str, cause_id: str, day: date) -> None:
        e = Event(len(evs) + 1, state, cause_kind, cause_id, day)
        evs.append(e)
        plan.events.append(e)
        done.add((cause_kind, cause_id))

    def maybe_close(before: date | None) -> None:
        h = head()
        if h is None or h.state != "RESOLVED_MONITORING":
            return
        days = [d for d in clean if d > h.effective_day and (before is None or d < before)]
        if len(days) >= close_after:
            nth = days[close_after - 1]
            cause_id = f"{thread_id}:{nth.isoformat()}"
            if ("CLEAN_DAYS", cause_id) not in done:
                add("CLOSED", "CLEAN_DAYS", cause_id, nth)

    for c in sorted(causes, key=lambda c: (c.effective_day, c.recorded_at, c.cause_id)):
        if (c.cause_kind, c.cause_id) in done:
            continue
        maybe_close(c.effective_day)
        h = head()
        state = None if h is None else h.state
        target = TRANSITIONS.get((state, c.cause))
        reason = None
        if h is not None and c.cause != OCCURRENCE and c.effective_day < h.effective_day:
            # A cause dated before the head was already judged against an earlier head (applied or skipped) in a
            # previous run, or in this one; judging it again against a later head would make a rerun write.
            reason = "BEFORE_HEAD"
        elif target is None:
            if c.cause == OCCURRENCE:
                continue  # an occurrence on a thread that is not resolved adds no event (CH-2 "ADDED")
            reason = "ILLEGAL_TRANSITION"
        elif c.cause == OCCURRENCE and h is not None and c.effective_day <= h.effective_day:
            continue  # only an occurrence after the verified (or closed) day is a recurrence
        elif c.cause in ACTION_CAUSES:
            if c.action_id not in actions:
                reason = "ACTION_NOT_ON_THREAD"
            else:
                seg = action_segment(evs, occ_by_source.get(actions[c.action_id]), accepted_day.get(c.action_id))
                if seg != segment_on(evs, None):
                    reason = "EARLIER_SEGMENT"
        elif c.cause == SUPPORT_LOST and actions:
            reason = "ACTION_ON_THREAD"
        if reason is not None:
            plan.skipped.append({"thread_id": thread_id, "cause": c.cause, "cause_id": c.cause_id,
                                 "from_state": state, "reason": reason})
            continue
        add(target, c.cause_kind, c.cause_id, c.effective_day)  # type: ignore[arg-type]
    maybe_close(None)
    return plan


def complete_days(rows: Iterable[Any], subject_ref: str, measures: Sequence[str]) -> set[date]:
    """Days on which every listed measure has a row for the thread's subject (its asset, or the Site for a SITE
    measure) and every such row is COMPLETE (a PARTIAL day never counts; build sheet §2)."""
    if not measures:
        return set()
    by_day: dict[date, dict[str, list[str]]] = {}
    for r in rows:
        if r.measure not in measures:
            continue
        if r.subject_kind != "SITE" and str(r.subject_ref) != str(subject_ref):
            continue
        by_day.setdefault(r.local_day, {}).setdefault(r.measure, []).append(r.grade)
    return {d for d, per in by_day.items()
            if all(m in per for m in measures) and all(g == "COMPLETE" for gs in per.values() for g in gs)}


def fully_checked_days(rows: Iterable[Any], subject_ref: str, measures: Sequence[str],
                       occurrence_starts: Iterable[date | None] = ()) -> set[date]:
    """CH3-R: the one definition of a "fully checked day", for the close rule (CLEAN_DAYS) and for the board's
    "{k} more fully checked days to close" count alike: every clean-day measure snapshot of the thread's subject is
    COMPLETE that day, and no occurrence of the thread started that day."""
    return complete_days(rows, subject_ref, measures) - {d for d in occurrence_starts if d is not None}


def thread_view(events: Sequence[Event], occ: Occurrence, day: date | None, known_at: datetime | None,
                complete: Iterable[date] = (), close_after: int = 7) -> dict[str, Any]:
    """The read-time view of one Finding's thread on a board day (build sheet §3, §5): its segment, the state and
    effective day in that segment, the change day, and the fully checked days since the verified day. `complete`
    holds the thread's fully checked days (`fully_checked_days`), the same days the close rule counts."""
    evs = visible(events, known_at)
    seg = occurrence_segment(evs, occ)
    mine = [e for e in evs if segment_of_event(evs, e.seq) == seg]
    on = day if day is not None else date.max
    state, eff = state_on(evs, on, seg)
    change = [e.effective_day for e in mine if e.state == "CHANGE_APPLIED"]
    verified = [e.effective_day for e in mine if e.state == "RESOLVED_MONITORING" and e.effective_day <= on]
    closed = [e.effective_day for e in mine if e.state == "CLOSED" and e.effective_day <= on]
    complete = sorted(set(complete))
    since = verified[-1] if verified else None
    checked = [d for d in complete if since is not None and since < d <= on]
    return {"segment_no": seg, "state": state, "state_effective_day": eff,
            "segment_current": segment_on(evs, on),
            "change_day": change[0] if change else None,
            "first_complete_after_change": next((d for d in complete if change and d >= change[0]), None),
            "checked_days": len(checked), "close_after": close_after,
            "recurred_day": eff if state == "RECURRED" else None,
            "closed_day": closed[-1] if closed else None,
            "events": [(e.seq, e.state, e.effective_day) for e in mine]}


def plus_days(at: datetime, days: int) -> datetime:
    return at + timedelta(days=days)
