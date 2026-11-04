"""CH-2 ThreadRegistry (design §5.2 A2; build sheet CH-2 §3): the pure placement core.

A thread is keyed by `(tenant, site, mechanism, subject_kind, subject_ref)`, all read from stored columns (ruling R4;
DS-R1 item 3): the mini-grid generator, the cold or EV subject asset, or the Site for a productive-use headroom
opportunity (R3). A thread stores its mechanism and finding type only; which outcomes it moves stays declared in
`outcomes/outcome_map.py` (OL-1), so nothing here names an outcome.

`plan_place` turns one source revision into the rows to append; `ThreadRegistry` applies plans over a port with no
SQL of its own. Thread ids are uuid5 of the key, so two runs produce identical rows and a second run writes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable, Protocol
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

#: The fixed uuid5 namespace of thread ids (never change it: ids are derived, not stored elsewhere).
NAMESPACE = UUID("6a1c3c2e-6f0e-5b8e-9d3c-2c4b1f0a7e42")
POLICY_VERSION = "thread-lifecycle/1"
EVIDENCE_CLASS = "MEASURED"  # design §4.3: every type placed today is measured
OPP_MECHANISM = "PRODUCTIVE_USE_HEADROOM"
OPP_FINDING_TYPE = "PRODUCTIVE_USE_HEADROOM@1"
#: CH4-R R1 (DS-R1): a study is a Source only with at least this many eligible days
#: -> catalogue `finding_types.PRODUCTIVE_USE_HEADROOM@1.rule` (CH-8).
OPP_MIN_ELIGIBLE_DAYS = 1

#: Subject mapping (build sheet §3, R4). A further domain needs one row here, nothing else.
SUBJECT_COLUMN = {"mini_grid": "generator_asset_id", "cold_chain": "subject_asset_id",
                  "ev_charging": "subject_asset_id"}

RECURS_FROM = ("RESOLVED_MONITORING", "CLOSED")
OPENS_FROM = (None, "WITHDRAWN")

ACTION_KINDS = ("MINI_TRIAL", "DOMAIN_INTENT")
LINKED = "LINKED"
ALREADY_LINKED = "ALREADY_LINKED"
PENDING_PLACEMENT = "PENDING_PLACEMENT"


@dataclass(frozen=True)
class Source:
    """One Finding revision or one opportunity revision, as the reader port reads it."""
    tenant_id: UUID
    site_id: UUID
    site_tz: str
    finding_id: UUID | None
    opportunity_id: UUID | None
    mechanism: str
    subject_kind: str
    subject_ref: str
    finding_type: str
    transition: str | None          # finding_revision.transition; None for an opportunity
    lifecycle: str | None
    episode_start: datetime | None
    episode_end: datetime | None
    created_at: datetime
    revision_id: UUID

    @property
    def source_id(self) -> UUID:
        return self.finding_id if self.finding_id is not None else self.opportunity_id  # type: ignore[return-value]


@dataclass(frozen=True)
class ThreadHead:
    id: UUID
    occurrences: int
    state: str | None   # the latest event's state; None when the thread has no event
    events: int


@dataclass(frozen=True)
class PlacePlan:
    action: str                              # NOOP | PLACE
    thread_id: UUID
    create_thread: dict[str, Any] | None = None
    occurrence: dict[str, Any] | None = None
    event: dict[str, Any] | None = None
    reason: str = ""


#: CH5a2-R R3 (CH-5a2b): the three thread classes of the count claims and `thread_progress`.
OPEN_CLASS = ("OPEN", "RECURRED", "REOPENED")
IN_HAND_CLASS = ("ACTION_IN_HAND", "CHANGE_APPLIED")
VERIFIED_CLASS = ("RESOLVED_MONITORING", "CLOSED")


def classify(states: Iterable[str | None]) -> dict[str, int]:
    """The one thread classifier (§B13 R3, §B14 Q7): open, in hand and verified counts over one state per thread."""
    out = {"open": 0, "in_hand": 0, "verified": 0}
    for st in states:
        if st in OPEN_CLASS:
            out["open"] += 1
        elif st in IN_HAND_CLASS:
            out["in_hand"] += 1
        elif st in VERIFIED_CLASS:
            out["verified"] += 1
    return out


def finding_source(row: dict[str, Any]) -> Source:
    """A Finding revision row (finding columns + revision columns + `site_tz`) -> its Source, keyed from stored
    columns only. Raises KeyError for a domain without a mapping row (a fourth domain adds one)."""
    column = SUBJECT_COLUMN[row["domain"]]
    subject = row[column]
    if subject is None:
        raise ValueError(f"Finding {row['finding_id']} has no {column}")
    mechanism = row["mechanism"]
    return Source(UUID(str(row["tenant_id"])), UUID(str(row["site_id"])), row["site_tz"], UUID(str(row["finding_id"])),
                  None, mechanism, "ASSET", str(subject), f"{mechanism}@{row['matcher_version']}",
                  row.get("transition"), row.get("lifecycle"), row.get("episode_start"), row.get("episode_end"),
                  row["created_at"], UUID(str(row["revision_id"])))


def _eligible_days(day_rows: Any) -> list[date]:
    """The `ELIGIBLE` Site-local days of a stored `day_rows` array (ISO strings or dates), sorted."""
    out = []
    for r in day_rows or ():
        if isinstance(r, dict) and r.get("decision") == "ELIGIBLE" and r.get("local_day") is not None:
            d = r["local_day"]
            out.append(d if isinstance(d, date) else date.fromisoformat(str(d)))
    return sorted(out)


def opportunity_source(row: dict[str, Any]) -> Source | None:
    """An opportunity revision row -> its Source on the Site's headroom thread (ruling R3), or None when the
    revision is not a Source (CH4-R R1, DS-R1: below `OPP_MIN_ELIGIBLE_DAYS` eligible days).

    CH4-R R2 (refines CH2-R M1): the episode is the eligible days, stored story time: the Site-local start of the
    first `ELIGIBLE` `day_rows[].local_day` through the start of the day after the last one (exclusive), so
    `opened_at` and `effective_day` are never build time and never a day before anything was seen. The study window
    stays on the opportunity (`first_day`/`last_day`). A row without eligible day rows falls back to `created_at`."""
    eligible = row.get("eligible_days")
    if eligible is None or int(eligible) < OPP_MIN_ELIGIBLE_DAYS:
        return None
    start = end = None
    days = _eligible_days(row.get("day_rows"))
    if days:
        tz = ZoneInfo(row["site_tz"])
        start = datetime.combine(days[0], time.min, tzinfo=tz)
        end = datetime.combine(days[-1] + timedelta(days=1), time.min, tzinfo=tz)
    return Source(UUID(str(row["tenant_id"])), UUID(str(row["site_id"])), row["site_tz"], None,
                  UUID(str(row["opportunity_id"])), OPP_MECHANISM, "SITE", "SITE", OPP_FINDING_TYPE, None, None,
                  start, end, row["created_at"], UUID(str(row["revision_id"])))


def key_of(src: Source) -> tuple[UUID, UUID, str, str, str]:
    return (src.tenant_id, src.site_id, src.mechanism, src.subject_kind, src.subject_ref)


def thread_id_of(key: tuple[UUID, UUID, str, str, str]) -> UUID:
    return uuid5(NAMESPACE, "thread|" + "|".join(str(part) for part in key))


def effective_day(src: Source) -> date:
    """AG-27: the Site-local day (`site.timezone`) of the episode start, else of the revision's creation."""
    at = src.episode_start if src.episode_start is not None else src.created_at
    return at.astimezone(ZoneInfo(src.site_tz)).date()


def order_key(src: Source) -> tuple[datetime, str]:
    """Ruling R2: sources are applied by `(created_at, revision id)`."""
    return (src.created_at, str(src.revision_id))


def plan_place(src: Source, existing_occurrence: bool, thread: ThreadHead | None) -> PlacePlan:
    """A2: the rows one source revision appends. A source already placed, or a MERGED_INTO revision, is a NOOP."""
    tid = thread.id if thread is not None else thread_id_of(key_of(src))
    if existing_occurrence:
        return PlacePlan("NOOP", tid, reason="ALREADY_PLACED")
    if src.transition == "MERGED_INTO":
        return PlacePlan("NOOP", tid, reason="MERGED_INTO")
    occurrence = {"tenant_id": src.tenant_id, "site_id": src.site_id, "thread_id": tid,
                  "occurrence_no": 1 if thread is None else thread.occurrences + 1,
                  "finding_id": src.finding_id, "opportunity_id": src.opportunity_id,
                  "episode_start": src.episode_start, "episode_end": src.episode_end,
                  "evidence_class": EVIDENCE_CLASS,
                  "time_basis": "story_time" if src.episode_start is not None else "recorded_at",
                  "source_known_at": src.created_at}  # CH3-R D-b (0045): the revision's own recorded time

    def event(state: str) -> dict[str, Any]:
        return {"tenant_id": src.tenant_id, "site_id": src.site_id, "thread_id": tid,
                "seq": 1 if thread is None else thread.events + 1, "state": state, "cause_kind": "OCCURRENCE",
                "cause_id": str(src.source_id), "effective_day": effective_day(src), "policy_version": POLICY_VERSION,
                "cause_known_at": src.created_at}

    if thread is None:
        create = {"id": tid, "tenant_id": src.tenant_id, "site_id": src.site_id, "mechanism": src.mechanism,
                  "subject_kind": src.subject_kind, "subject_ref": src.subject_ref, "finding_type": src.finding_type,
                  "opened_at": src.episode_start if src.episode_start is not None else src.created_at}
        return PlacePlan("PLACE", tid, create, occurrence, event("OPEN"), "NEW_THREAD")
    if thread.state in RECURS_FROM:
        return PlacePlan("PLACE", tid, None, occurrence, event("RECURRED"), "RECURRED")
    if thread.state in OPENS_FROM:
        return PlacePlan("PLACE", tid, None, occurrence, event("OPEN"), "OPENED")
    return PlacePlan("PLACE", tid, None, occurrence, None, "ADDED")


class ThreadPort(Protocol):
    def place(self, src: Source, plan_for: Any, created_by: str) -> PlacePlan: ...
    def link(self, kind: str, action_id: UUID, origin_finding_id: UUID, linked_by: str) -> str: ...


class MemoryThreads:
    """An in-memory port (the `--dry-run` mode and the pure tests): the same plans, applied to dictionaries."""

    def __init__(self) -> None:
        self.threads: dict[UUID, dict[str, Any]] = {}
        self.occurrences: dict[tuple[UUID, int], dict[str, Any]] = {}
        self.events: dict[tuple[UUID, int], dict[str, Any]] = {}
        self.links: dict[tuple[str, UUID], dict[str, Any]] = {}
        self._placed: dict[UUID, UUID] = {}  # source id -> thread id

    def head(self, tid: UUID) -> ThreadHead | None:
        if tid not in self.threads:
            return None
        occ = sum(1 for (t, _) in self.occurrences if t == tid)
        evs = sorted(n for (t, n) in self.events if t == tid)
        return ThreadHead(tid, occ, self.events[(tid, evs[-1])]["state"] if evs else None, len(evs))

    def place(self, src: Source, plan_for: Any, created_by: str) -> PlacePlan:
        plan = plan_for(src, src.source_id in self._placed, self.head(thread_id_of(key_of(src))))
        if plan.action == "PLACE":
            if plan.create_thread is not None:
                self.threads[plan.thread_id] = {**plan.create_thread, "created_by": created_by}
            o = plan.occurrence
            self.occurrences[(plan.thread_id, o["occurrence_no"])] = o
            self._placed[src.source_id] = plan.thread_id
            if plan.event is not None:
                self.events[(plan.thread_id, plan.event["seq"])] = plan.event
        return plan

    def link(self, kind: str, action_id: UUID, origin_finding_id: UUID, linked_by: str) -> str:
        if (kind, action_id) in self.links:
            return ALREADY_LINKED
        tid = self._placed.get(origin_finding_id)
        if tid is None:
            return PENDING_PLACEMENT
        self.links[(kind, action_id)] = {"action_kind": kind, "action_id": action_id, "thread_id": tid,
                                         "origin_finding_id": origin_finding_id, "linked_by": linked_by}
        return LINKED

    # CH-3 §4: the lifecycle twin of PostgresThreadStore.site_threads / append_events / thread_head.
    def site_threads(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]:
        from assetops_backend.chain.lifecycle import Event
        out = []
        for tid, t in sorted(self.threads.items(), key=lambda kv: str(kv[0])):
            if str(t["site_id"]) != str(site_id):
                continue
            events = self.site_threads_events(tid)
            occs = [(str(o["finding_id"] or o["opportunity_id"]).lower(), o["episode_start"])
                    for (x, _), o in sorted(self.occurrences.items(), key=lambda kv: kv[0][1]) if x == tid]
            links = {str(link["action_id"]).lower(): str(link["origin_finding_id"]).lower()
                     for link in self.links.values() if link["thread_id"] == tid}
            known = {str(o["finding_id"] or o["opportunity_id"]).lower(): o.get("source_known_at")
                     for (x, _), o in self.occurrences.items() if x == tid}
            out.append({"id": tid, "mechanism": t["mechanism"], "subject_kind": t["subject_kind"],
                        "subject_ref": t["subject_ref"], "events": events, "occurrences": occs, "links": links,
                        "occurrence_known": known})
        return out

    def append_events(self, tenant_id: UUID, site_id: UUID, thread: dict[str, Any], planner: Any,
                      policy_version: str) -> Any:
        existing = self.site_threads_events(thread["id"])
        plan = planner(existing)
        for e in plan.events:
            self.events[(thread["id"], e.seq)] = {"tenant_id": tenant_id, "site_id": site_id, "thread_id": thread["id"],
                                                  "seq": e.seq, "state": e.state, "cause_kind": e.cause_kind,
                                                  "cause_id": e.cause_id, "effective_day": e.effective_day,
                                                  "policy_version": policy_version, "cause_known_at": e.known_at}
        return plan

    def site_threads_events(self, tid: UUID) -> list[Any]:
        from assetops_backend.chain.lifecycle import Event
        return [Event(e["seq"], e["state"], e["cause_kind"], e["cause_id"], e["effective_day"], None,
                      e.get("cause_known_at"))
                for (x, _), e in sorted(self.events.items(), key=lambda kv: kv[0][1]) if x == tid]

    def thread_head(self, tid: UUID) -> tuple[str | None, Any]:
        evs = self.site_threads_events(tid)
        return (None, None) if not evs else (evs[-1].state, evs[-1].effective_day)


@dataclass
class StepReport:
    step: str
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, key: str) -> None:
        self.counts[key] = self.counts.get(key, 0) + 1


class ThreadRegistry:
    """Applies placements and links over a port (Postgres, or `MemoryThreads` for a dry run)."""

    def __init__(self, port: ThreadPort, created_by: str = "backfill") -> None:
        self.port = port
        self.created_by = created_by

    def place_all(self, sources: Iterable[Source]) -> StepReport:
        report = StepReport("b")
        for src in sorted(sources, key=order_key):
            report.add(self.port.place(src, plan_place, self.created_by).reason)
        return report

    def link_all(self, actions: Iterable[dict[str, Any]]) -> StepReport:
        report = StepReport("c")
        for a in sorted(actions, key=lambda a: (a["kind"], str(a["id"]))):
            report.add(self.link_action(a["kind"], UUID(str(a["id"])), UUID(str(a["origin_finding_id"]))))
        return report

    def link_action(self, kind: str, action_id: UUID, origin_finding_id: UUID) -> str:
        """Writes the link to the thread holding `origin_finding_id`; PENDING_PLACEMENT (nothing written) when that
        Finding has no occurrence yet; idempotent on `(kind, action_id)`."""
        if kind not in ACTION_KINDS:
            raise ValueError(f"unknown Action kind {kind!r}")
        return self.port.link(kind, action_id, origin_finding_id, self.created_by)
