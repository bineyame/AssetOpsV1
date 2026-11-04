"""CH-2: the read-only thread source reader (build sheet CH-2 §3, a named `$pgReaders` module; no SQL write).

- `sources`: every Finding revision joined to its Finding, and every mini opportunity revision joined to its
  opportunity, with the Site's time zone, ordered by `(created_at, id)` (ruling R2).
- `unlinked_actions`: the `chain_action` rows with no thread link yet.
- `lookup`: the thread of each given Finding (id, occurrence number, occurrence count) and of each given Action,
  for the Site outcome board (one query per board).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from assetops_backend.chain.lookup import LOOKUP, OPPORTUNITY_LOOKUP, thread_lookup
from assetops_backend.chain.opportunities import opportunity_items
from assetops_backend.chain.threads import Source, finding_source, opportunity_source

_FINDING_SOURCES = (
    "SELECT r.tenant_id, r.site_id, s.timezone AS site_tz, f.id AS finding_id, f.domain, f.mechanism, "
    "f.matcher_version, f.generator_asset_id, CAST(f.subject_asset_id AS text) AS subject_asset_id, "
    "r.transition, r.lifecycle, r.episode_start, r.episode_end, r.created_at, r.id AS revision_id "
    "FROM finding_revision r JOIN finding f ON f.tenant_id = r.tenant_id AND f.site_id = r.site_id "
    "AND f.id = r.finding_id JOIN site s ON s.tenant_id = r.tenant_id AND s.id = r.site_id "
    "WHERE r.tenant_id = :t AND (CAST(:s AS uuid) IS NULL OR r.site_id = CAST(:s AS uuid)) "
    "AND (CAST(:after AS timestamptz) IS NULL OR r.created_at > CAST(:after AS timestamptz)) "
    "ORDER BY r.created_at, r.id")

_OPPORTUNITY_SOURCES = (
    "SELECT r.tenant_id, r.site_id, s.timezone AS site_tz, o.id AS opportunity_id, o.first_day, o.last_day, "
    "r.created_at, r.id AS revision_id, CAST(r.result->>'eligible_days' AS int) AS eligible_days, "
    "r.result->'day_rows' AS day_rows FROM mini_opportunity_revision r JOIN mini_opportunity o ON o.tenant_id = r.tenant_id "
    "AND o.site_id = r.site_id AND o.id = r.opportunity_id JOIN site s ON s.tenant_id = r.tenant_id "
    "AND s.id = r.site_id WHERE r.tenant_id = :t AND (CAST(:s AS uuid) IS NULL OR r.site_id = CAST(:s AS uuid)) "
    "AND (CAST(:after AS timestamptz) IS NULL OR r.created_at > CAST(:after AS timestamptz)) "
    "ORDER BY r.created_at, r.id")

_UNLINKED = (
    "SELECT id, tenant_id, site_id, action_code, kind, origin_finding_id FROM chain_action "
    "WHERE thread_id IS NULL AND tenant_id = :t AND (CAST(:s AS uuid) IS NULL OR site_id = CAST(:s AS uuid)) "
    "ORDER BY kind, id")

# CH-1b §3 (the event-driven `chain_threads` stage): the same rows, restricted to the revision ids an outbox event
# names; and the unlinked Actions an event names, or whose origin Finding a placement just put on a thread.
_ONLY_REVISIONS = "AND r.id = ANY(CAST(:ids AS uuid[])) ORDER BY r.created_at, r.id"
_FINDING_SOURCES_BY_ID = _FINDING_SOURCES.replace("ORDER BY r.created_at, r.id", _ONLY_REVISIONS)
_OPPORTUNITY_SOURCES_BY_ID = _OPPORTUNITY_SOURCES.replace("ORDER BY r.created_at, r.id", _ONLY_REVISIONS)
_UNLINKED_FOR = _UNLINKED.replace(
    "ORDER BY kind, id",
    "AND (id = ANY(CAST(:a AS uuid[])) OR origin_finding_id = ANY(CAST(:f AS uuid[]))) ORDER BY kind, id")

# CH-3 §4: the lifecycle causes of one Site (SELECT only).
_CHANGE_OF = ("(SELECT c.effective_from FROM action_policy_change c WHERE c.tenant_id = {a}.tenant_id "
              "AND c.action_id = {a}.action_id ORDER BY c.recorded_at DESC, c.id DESC LIMIT 1)")
_ACTION_EVENTS = (
    "SELECT e.id, e.action_id, e.kind, e.recorded_at, " + _CHANGE_OF.format(a="e") + " AS effective_from "
    "FROM action_event e WHERE e.tenant_id = :t AND e.site_id = :s "
    "AND e.kind IN ('ACCEPTED','APPLIED','RESOLUTION_WITHDRAWN') ORDER BY e.recorded_at, e.id")
_OUTCOMES = (
    "SELECT o.id, o.action_id, o.outcome, o.recorded_at, p.later_end, " + _CHANGE_OF.format(a="o") +
    " AS effective_from, EXISTS (SELECT 1 FROM verification_outcome x WHERE x.supersedes_outcome_id = o.id) "
    "AS superseded FROM verification_outcome o JOIN verification_plan p ON p.id = o.plan_id "
    "WHERE o.tenant_id = :t AND o.site_id = :s ORDER BY o.recorded_at, o.id")
_DOMAIN_ACTIONS = "SELECT id, recorded_at FROM domain_action WHERE tenant_id = :t AND site_id = :s"
_CASE_COMPLETIONS = (
    "SELECT DISTINCT w.id, l.action_id, w.occurred_at, w.recorded_at FROM domain_action_case_link l "
    "JOIN work_event w ON w.tenant_id = l.tenant_id AND w.site_id = l.site_id AND w.case_id = l.case_id "
    "AND w.kind = 'COMPLETE' WHERE l.tenant_id = :t AND l.site_id = :s")
_FINDING_LIFECYCLE = (
    "SELECT DISTINCT ON (r.finding_id) CAST(r.finding_id AS text) AS finding_id, r.lifecycle, r.id AS revision_id, "
    "r.created_at FROM finding_revision r WHERE r.tenant_id = :t AND r.site_id = :s "
    "ORDER BY r.finding_id, r.created_at DESC, r.id DESC")
# CH4-R R6: each opportunity's selected head revision now (its eligible days decide SUPPORT_LOST).
_OPPORTUNITY_HEADS = (
    "SELECT DISTINCT ON (x.opportunity_id) CAST(x.opportunity_id AS text) AS opportunity_id, r.id AS revision_id, "
    "r.created_at, CAST(r.result->>'eligible_days' AS int) AS eligible_days FROM mini_opportunity_selection x "
    "JOIN mini_opportunity_revision r ON r.tenant_id = x.tenant_id AND r.id = x.revision_id "
    "WHERE x.tenant_id = :t AND r.site_id = :s ORDER BY x.opportunity_id, x.selected_at DESC, x.seq DESC")
_SNAPSHOTS = (
    "SELECT DISTINCT ON (measure, local_day, subject_kind, subject_ref) local_day, subject_kind, subject_ref, "
    "measure, grade FROM site_day_snapshot WHERE tenant_id = :t AND site_id = ANY(CAST(:sites AS uuid[])) "
    "AND measure = ANY(CAST(:m AS text[])) ORDER BY measure, local_day, subject_kind, subject_ref, revision DESC")


class _Snap:
    __slots__ = ("site_id", "local_day", "subject_kind", "subject_ref", "measure", "grade")

    def __init__(self, r: Any) -> None:
        for k in self.__slots__:
            setattr(self, k, r.get(k))


class PostgresThreadSources:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise RuntimeError("DATABASE_URL is not set, so the thread sources cannot be read.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _rows(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        with self._connect().connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                return [dict(r) for r in c.execute(text(sql), params).mappings()]

    def database_name(self) -> str:
        return self._connect().url.database or ""

    def tenant_id(self, slug: str) -> UUID | None:
        rows = self._rows("SELECT id FROM tenant WHERE slug = :slug", {"slug": slug})
        return rows[0]["id"] if rows else None

    def site_ids(self, tenant_id: UUID, site_code: str | None = None) -> list[tuple[UUID, str]]:
        rows = self._rows("SELECT id, site_code FROM site WHERE tenant_id = :t AND (CAST(:c AS text) IS NULL "
                          "OR site_code_key = lower(CAST(:c AS text))) ORDER BY site_code_key",
                          {"t": tenant_id, "c": site_code})
        return [(r["id"], r["site_code"]) for r in rows]

    def sources(self, tenant_id: UUID, site_id: UUID | None = None,
                after: datetime | None = None) -> list[Source | None]:
        """Sources in `(created_at, id)` order, then one None per opportunity revision that is not a Source
        (CH4-R R1: below the eligible-day minimum); the callers skip and count them (`skipped_ineligible`)."""
        p = {"t": tenant_id, "s": None if site_id is None else str(site_id), "after": after}
        out: list[Source | None] = [finding_source(r) for r in self._rows(_FINDING_SOURCES, p)]
        out += [opportunity_source(r) for r in self._rows(_OPPORTUNITY_SOURCES, p)]
        placed = sorted((s for s in out if s is not None), key=lambda s: (s.created_at, str(s.revision_id)))
        return [*placed, *([None] * (len(out) - len(placed)))]

    def unlinked_actions(self, tenant_id: UUID, site_id: UUID | None = None) -> list[dict[str, Any]]:
        return self._rows(_UNLINKED, {"t": tenant_id, "s": None if site_id is None else str(site_id)})

    def sources_by_revision(self, tenant_id: UUID, site_id: UUID, finding_revision_ids: Sequence[Any],
                            opportunity_revision_ids: Sequence[Any]) -> list[Source]:
        """CH-1b: only the named Finding and opportunity revisions of this Site, in `(created_at, id)` order."""
        p = {"t": tenant_id, "s": str(site_id), "after": None}
        out: list[Source] = []
        if finding_revision_ids:
            out += [finding_source(r) for r in self._rows(
                _FINDING_SOURCES_BY_ID, {**p, "ids": [str(i) for i in finding_revision_ids]})]
        if opportunity_revision_ids:
            out += [opportunity_source(r) for r in self._rows(
                _OPPORTUNITY_SOURCES_BY_ID, {**p, "ids": [str(i) for i in opportunity_revision_ids]})]
        return sorted(out, key=lambda s: (s.created_at, str(s.revision_id)))

    def unlinked_actions_for(self, tenant_id: UUID, site_id: UUID, action_ids: Sequence[Any],
                             finding_ids: Sequence[Any]) -> list[dict[str, Any]]:
        """CH-1b: this Site's unlinked Actions named by an event, or whose origin Finding was just placed (an Action
        recorded before its Finding's placement stays PENDING_PLACEMENT until then)."""
        if not action_ids and not finding_ids:
            return []
        return self._rows(_UNLINKED_FOR, {"t": tenant_id, "s": str(site_id), "a": [str(i) for i in action_ids],
                                          "f": [str(i) for i in finding_ids]})

    def all_actions(self, tenant_id: UUID, site_id: UUID | None = None) -> list[dict[str, Any]]:
        """Both Action tables directly (the `--dry-run` mode: it also reads a database below 0042)."""
        return self._rows(
            "SELECT id, tenant_id, site_id, action_code, 'MINI_TRIAL' AS kind, origin_finding_id FROM action "
            "WHERE tenant_id = :t AND (CAST(:s AS uuid) IS NULL OR site_id = CAST(:s AS uuid)) UNION ALL "
            "SELECT id, tenant_id, site_id, action_code, 'DOMAIN_INTENT', origin_finding_id FROM domain_action "
            "WHERE tenant_id = :t AND (CAST(:s AS uuid) IS NULL OR site_id = CAST(:s AS uuid)) ORDER BY 5, 1",
            {"t": tenant_id, "s": None if site_id is None else str(site_id)})

    def lifecycle_inputs(self, tenant_id: UUID, site_id: UUID) -> dict[str, Any]:
        """CH-3 §4: everything `run_lifecycle` reads for one Site, in one READ ONLY transaction."""
        from assetops_backend.chain.adapters.file_chain_config import load_thread_lifecycle
        measures = sorted({m for ms in load_thread_lifecycle().clean_day_measures.values() for m in ms})
        p = {"t": tenant_id, "s": site_id}
        with self._connect().connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                tz, now, site_type = c.execute(text(
                    "SELECT s.timezone, now(), s.site_type FROM site s WHERE s.tenant_id = :t AND s.id = :s"), p).one()

                def rows(sql: str) -> list[dict[str, Any]]:
                    return [dict(r) for r in c.execute(text(sql), p).mappings()]

                out = {"tz": tz, "now": now, "site_type": site_type, "action_events": rows(_ACTION_EVENTS), "outcomes": rows(_OUTCOMES),
                       "domain_actions": rows(_DOMAIN_ACTIONS), "case_completions": rows(_CASE_COMPLETIONS),
                       "finding_lifecycle": {r["finding_id"].lower(): r for r in rows(_FINDING_LIFECYCLE)},
                       "opportunity_heads": {r["opportunity_id"].lower(): r for r in rows(_OPPORTUNITY_HEADS)},
                       "snapshots": []}
                if not c.execute(text("SELECT to_regclass('site_day_snapshot') IS NULL")).scalar_one():
                    out["snapshots"] = [_Snap(dict(r)) for r in c.execute(
                        text(_SNAPSHOTS), {"t": tenant_id, "sites": [str(site_id)], "m": measures}).mappings()]
        return out

    def opportunity_labels(self, tenant_id: UUID) -> dict[str, str]:
        rows = self._rows("SELECT id, public_no FROM mini_opportunity WHERE tenant_id = :t", {"t": tenant_id})
        return {str(r["id"]): f"OPP-{int(r['public_no']):06d}" for r in rows}

    def opportunity_threads(self, tenant_id: Any, site_ids: Sequence[Any], from_: datetime, to: datetime,
                            k: datetime | None) -> list[dict[str, Any]]:
        """CH-4 §3: the opportunity items of the given Sites seen in `[from_, to)` as of `k` (the estate snapshot
        runs the same `OPPORTUNITY_LOOKUP` text). Below 0042 there are none."""
        from assetops_backend.chain.adapters.file_chain_config import load_thread_lifecycle
        if not site_ids:
            return []
        with self._connect().connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                if c.execute(text("SELECT to_regclass('chain_action_thread') IS NULL")).scalar_one():
                    return []
                rows = c.execute(text(OPPORTUNITY_LOOKUP), {"t": tenant_id, "s": [str(x).lower() for x in site_ids],
                                                            "k": k}).all()
        return opportunity_items(rows, from_, to, k, load_thread_lifecycle().close_after)

    def lookup(self, tenant_id: Any, finding_ids: Sequence[Any], action_ids: Sequence[Any], *,
               day: Any = None, known_at: datetime | None = None, site_id: Any = None,
               opportunity_window: tuple[datetime, datetime] | None = None) -> dict[str, Any]:
        """CH-2 §5.2 / CH-3 §3, §5: one thread lookup per board, with each Finding's state on the board `day` as of
        `known_at`, and the COMPLETE days of its clean-day measures (CH-1a snapshots; none below 0043). CH-4 §4.4:
        with `site_id` and `opportunity_window` (a mini board's renewable five days), `"opportunities"` holds the
        Site's opportunity items seen in that window as of `known_at`."""
        opps: list[dict[str, Any]] = []
        if site_id is not None and opportunity_window is not None:
            opps = self.opportunity_threads(tenant_id, [site_id], opportunity_window[0], opportunity_window[1],
                                            known_at)
        found = self._lookup(tenant_id, finding_ids, action_ids, day=day, known_at=known_at)
        return {**found, "opportunities": opps}

    def _lookup(self, tenant_id: Any, finding_ids: Sequence[Any], action_ids: Sequence[Any], *,
                day: Any = None, known_at: datetime | None = None) -> dict[str, Any]:
        from assetops_backend.chain.adapters.file_chain_config import load_thread_lifecycle
        from assetops_backend.chain.lifecycle import fully_checked_days, local_day
        policy = load_thread_lifecycle()
        if not finding_ids and not action_ids:
            return thread_lookup([])
        with self._connect().connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                if c.execute(text("SELECT to_regclass('chain_action_thread') IS NULL")).scalar_one():
                    return thread_lookup([])  # a database below 0042 has no threads
                rows = c.execute(text(LOOKUP), {"t": tenant_id, "f": [str(x).lower() for x in finding_ids],
                                                "a": [str(x).lower() for x in action_ids]}).all()
                subjects = {r[1].lower(): (r[8], r[9]) for r in rows if r[0] == "F"}
                complete: dict[str, Any] = {}
                measures = sorted({m for mech, _ in subjects.values() for m in policy.measures_for(mech)})
                if subjects and measures and not c.execute(
                        text("SELECT to_regclass('site_day_snapshot') IS NULL")).scalar_one():
                    snap = [_Snap(dict(r)) for r in c.execute(text(
                        "SELECT DISTINCT ON (measure, local_day, subject_kind, subject_ref) local_day, subject_kind, "
                        "subject_ref, measure, grade FROM site_day_snapshot WHERE tenant_id = :t AND site_id IN "
                        "(SELECT site_id FROM finding_thread_occurrence WHERE CAST(finding_id AS text) = "
                        "ANY(CAST(:f AS text[]))) AND measure = ANY(CAST(:m AS text[]))"
                        + ("" if known_at is None else " AND computed_at <= :k") +
                        " ORDER BY measure, local_day, subject_kind, subject_ref, revision DESC"),
                        {"t": tenant_id, "f": list(subjects), "m": measures, "k": known_at}).mappings()]
                    # CH3-R: one "fully checked day" rule with the close rule (no occurrence of the thread started)
                    threads = {r[1].lower(): str(r[2]) for r in rows if r[0] == "F"}
                    starts: dict[str, list[Any]] = {}
                    for tid, start, tz in c.execute(text(
                            "SELECT CAST(o.thread_id AS text), o.episode_start, s.timezone FROM "
                            "finding_thread_occurrence o JOIN site s ON s.tenant_id = o.tenant_id AND s.id = o.site_id "
                            "WHERE o.tenant_id = :t AND CAST(o.thread_id AS text) = ANY(CAST(:th AS text[]))"
                            + ("" if known_at is None else " AND coalesce(o.source_known_at, o.joined_at) <= :k")),
                            {"t": tenant_id, "th": sorted(set(threads.values())), "k": known_at}).all():
                        if start is not None and tz:
                            starts.setdefault(tid, []).append(local_day(start, tz))
                    complete = {fid: fully_checked_days(snap, subject, policy.measures_for(mech),
                                                        starts.get(threads[fid], ()))
                                for fid, (mech, subject) in subjects.items()}
        return thread_lookup(rows, day=day, known_at=known_at, complete=complete, close_after=policy.close_after)
