"""CH-2 / CH-3: the sole writer of `finding_thread`, `finding_thread_occurrence`, `finding_thread_event` and
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

from assetops_backend.chain.lifecycle import Event
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
    "opportunity_id, episode_start, episode_end, evidence_class, time_basis) VALUES (:tenant_id, :site_id, :thread_id, "
    ":occurrence_no, :finding_id, :opportunity_id, :episode_start, :episode_end, :evidence_class, :time_basis)")

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


_SITE_THREADS = text(
    "SELECT id, mechanism, subject_kind, subject_ref FROM finding_thread WHERE tenant_id = :t AND site_id = :s "
    "ORDER BY id")

_SITE_EVENTS = text(
    "SELECT thread_id, seq, state, cause_kind, cause_id, effective_day, recorded_at FROM finding_thread_event "
    "WHERE tenant_id = :t AND site_id = :s ORDER BY thread_id, seq")

_SITE_OCCURRENCES = text(
    "SELECT thread_id, CAST(COALESCE(finding_id, opportunity_id) AS text) AS source_id, episode_start "
    "FROM finding_thread_occurrence WHERE tenant_id = :t AND site_id = :s ORDER BY thread_id, occurrence_no")

_SITE_LINKS = text(
    "SELECT thread_id, CAST(action_id AS text) AS action_id, CAST(origin_finding_id AS text) AS origin "
    "FROM chain_action_thread WHERE tenant_id = :t AND site_id = :s")

_THREAD_EVENTS = text(
    "SELECT seq, state, cause_kind, cause_id, effective_day, recorded_at FROM finding_thread_event "
    "WHERE thread_id = :id ORDER BY seq")


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

    # CH-3 §4: the lifecycle reads and the event append. The append takes the same per-key advisory lock as
    # `place()`, re-reads the thread's events inside it, asks the pure planner for the rows and inserts them; a
    # concurrent placement or lifecycle run on the key serialises behind it.
    def site_threads(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]:
        p = {"t": tenant_id, "s": site_id}
        with self._connect().connect() as c:
            with c.begin():
                if c.execute(text("SELECT to_regclass('finding_thread_event') IS NULL")).scalar_one():
                    return []
                threads = [dict(r) for r in c.execute(_SITE_THREADS, p).mappings()]
                events = c.execute(_SITE_EVENTS, p).mappings().all()
                occs = c.execute(_SITE_OCCURRENCES, p).mappings().all()
                links = c.execute(_SITE_LINKS, p).mappings().all()
        for t in threads:
            t["events"] = [Event(e["seq"], e["state"], e["cause_kind"], e["cause_id"], e["effective_day"],
                                 e["recorded_at"]) for e in events if e["thread_id"] == t["id"]]
            t["occurrences"] = [(o["source_id"].lower(), o["episode_start"]) for o in occs if o["thread_id"] == t["id"]]
            t["links"] = {x["action_id"].lower(): x["origin"].lower() for x in links if x["thread_id"] == t["id"]}
        return threads

    def append_events(self, tenant_id: UUID, site_id: UUID, thread: dict[str, Any],
                      planner: Callable[[list[Event]], Any], policy_version: str) -> Any:
        key = (tenant_id, site_id, thread["mechanism"], thread["subject_kind"], thread["subject_ref"])

        def work(c: Connection) -> Any:
            c.execute(_LOCK, {"k": "chain_thread|" + "|".join(str(p) for p in key)})
            existing = [Event(r["seq"], r["state"], r["cause_kind"], r["cause_id"], r["effective_day"],
                              r["recorded_at"]) for r in c.execute(_THREAD_EVENTS, {"id": thread["id"]}).mappings()]
            plan = planner(existing)
            for e in plan.events:
                c.execute(_INSERT_EVENT, {"tenant_id": tenant_id, "site_id": site_id, "thread_id": thread["id"],
                                          "seq": e.seq, "state": e.state, "cause_kind": e.cause_kind,
                                          "cause_id": e.cause_id, "effective_day": e.effective_day,
                                          "policy_version": policy_version})
            return plan

        return self._tx(work)

    def thread_head(self, thread_id: UUID) -> tuple[str | None, Any]:
        with self._connect().connect() as c:
            row = c.execute(text("SELECT state, effective_day FROM finding_thread_event WHERE thread_id = :id "
                                 "ORDER BY seq DESC LIMIT 1"), {"id": thread_id}).first()
        return (None, None) if row is None else (row[0], row[1])
