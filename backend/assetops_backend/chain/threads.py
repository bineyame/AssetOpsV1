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


def opportunity_source(row: dict[str, Any]) -> Source:
    """An opportunity revision row -> its Source on the Site's headroom thread (ruling R3).

    DS-R1 item 4: the episode is the stored study window, the Site-local start of `first_day` through the end of
    `last_day` (the start of the next local day, exclusive), so `opened_at` and `effective_day` are story time, not
    build time. A row without the window (no stored story time) falls back to `created_at` as before."""
    start = end = None
    first, last = row.get("first_day"), row.get("last_day")
    if first is not None and last is not None:
        tz = ZoneInfo(row["site_tz"])
        start = datetime.combine(first, time.min, tzinfo=tz)
        end = datetime.combine(last + timedelta(days=1), time.min, tzinfo=tz)
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
                  "time_basis": "story_time" if src.episode_start is not None else "recorded_at"}

    def event(state: str) -> dict[str, Any]:
        return {"tenant_id": src.tenant_id, "site_id": src.site_id, "thread_id": tid,
                "seq": 1 if thread is None else thread.events + 1, "state": state, "cause_kind": "OCCURRENCE",
                "cause_id": str(src.source_id), "effective_day": effective_day(src), "policy_version": POLICY_VERSION}

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
