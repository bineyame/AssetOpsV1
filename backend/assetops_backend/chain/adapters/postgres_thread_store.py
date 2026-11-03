"""CH-2: the sole writer of `finding_thread`, `finding_thread_occurrence`, `finding_thread_event` and
`chain_action_thread` (build sheet CH-2 §3, guard rule 8). Insert-only; the 0042 triggers refuse any other change.

One transaction per source: it takes a transaction advisory lock on the thread key, so two concurrent ticks placing
the same key serialise and the second sees the first's thread (one thread per key). It then re-reads whether the
source is already placed and the thread head, asks the pure `plan_place` for the rows, and inserts them.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from assetops_backend.chain.threads import (
    ALREADY_LINKED, LINKED, PENDING_PLACEMENT, PlacePlan, Source, ThreadHead, key_of, thread_id_of)

_LOCK = text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))")

_PLACED = text(
    "SELECT thread_id FROM finding_thread_occurrence WHERE finding_id = :f OR opportunity_id = :o")

_HEAD = text(
    "SELECT t.id, (SELECT count(*) FROM finding_thread_occurrence o WHERE o.thread_id = t.id) AS occurrences, "
    "(SELECT count(*) FROM finding_thread_event e WHERE e.thread_id = t.id) AS events, "
    "(SELECT e.state FROM finding_thread_event e WHERE e.thread_id = t.id ORDER BY e.seq DESC LIMIT 1) AS state "
    "FROM finding_thread t WHERE t.id = :id")

_INSERT_THREAD = text(
    "INSERT INTO finding_thread (id, tenant_id, site_id, mechanism, subject_kind, subject_ref, finding_type, "
    "opened_at, created_by) VALUES (:id, :tenant_id, :site_id, :mechanism, :subject_kind, :subject_ref, "
    ":finding_type, :opened_at, :created_by)")

_INSERT_OCCURRENCE = text(
    "INSERT INTO finding_thread_occurrence (tenant_id, site_id, thread_id, occurrence_no, finding_id, "
    "opportunity_id, episode_start, episode_end, evidence_class) VALUES (:tenant_id, :site_id, :thread_id, "
    ":occurrence_no, :finding_id, :opportunity_id, :episode_start, :episode_end, :evidence_class)")

_INSERT_EVENT = text(
    "INSERT INTO finding_thread_event (tenant_id, site_id, thread_id, seq, state, cause_kind, cause_id, "
    "effective_day, policy_version) VALUES (:tenant_id, :site_id, :thread_id, :seq, :state, :cause_kind, "
    ":cause_id, :effective_day, :policy_version)")

_LINKED = text("SELECT 1 FROM chain_action_thread WHERE action_kind = :kind AND action_id = :id")

_OCCURRENCE_OF = text(
    "SELECT tenant_id, site_id, thread_id FROM finding_thread_occurrence WHERE finding_id = :f")

_INSERT_LINK = text(
    "INSERT INTO chain_action_thread (tenant_id, site_id, action_kind, action_id, thread_id, origin_finding_id, "
    "linked_by) VALUES (:t, :s, :kind, :id, :thread, :f, :by)")


class ThreadStoreUnavailable(RuntimeError):
    pass


class PostgresThreadStore:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise ThreadStoreUnavailable("DATABASE_URL is not set, so the thread store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _tx(self, work: Callable[[Connection], Any]) -> Any:
        with self._connect().connect() as c:
            with c.begin():
                return work(c)

    def place(self, src: Source, plan_for: Callable[..., PlacePlan], created_by: str) -> PlacePlan:
        key = key_of(src)

        def work(c: Connection) -> PlacePlan:
            c.execute(_LOCK, {"k": "chain_thread|" + "|".join(str(p) for p in key)})
            placed = c.execute(_PLACED, {"f": src.finding_id, "o": src.opportunity_id}).first() is not None
            row = c.execute(_HEAD, {"id": thread_id_of(key)}).mappings().first()
            head = None if row is None else ThreadHead(row["id"], int(row["occurrences"]), row["state"],
                                                       int(row["events"]))
            plan = plan_for(src, placed, head)
            if plan.action == "PLACE":
                if plan.create_thread is not None:
                    c.execute(_INSERT_THREAD, {**plan.create_thread, "created_by": created_by})
                c.execute(_INSERT_OCCURRENCE, plan.occurrence)
                if plan.event is not None:
                    c.execute(_INSERT_EVENT, plan.event)
            return plan

        return self._tx(work)

    def link(self, kind: str, action_id: UUID, origin_finding_id: UUID, linked_by: str) -> str:
        def work(c: Connection) -> str:
            c.execute(_LOCK, {"k": f"chain_link|{kind}|{action_id}"})
            if c.execute(_LINKED, {"kind": kind, "id": action_id}).first() is not None:
                return ALREADY_LINKED
            occ = c.execute(_OCCURRENCE_OF, {"f": origin_finding_id}).first()
            if occ is None:
                return PENDING_PLACEMENT
            c.execute(_INSERT_LINK, {"t": occ[0], "s": occ[1], "kind": kind, "id": action_id, "thread": occ[2],
                                     "f": origin_finding_id, "by": linked_by})
            return LINKED

        return self._tx(work)
