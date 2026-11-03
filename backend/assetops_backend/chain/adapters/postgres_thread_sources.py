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

from assetops_backend.chain.lookup import LOOKUP, thread_lookup
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
    "r.created_at, r.id AS revision_id FROM mini_opportunity_revision r JOIN mini_opportunity o ON o.tenant_id = r.tenant_id "
    "AND o.site_id = r.site_id AND o.id = r.opportunity_id JOIN site s ON s.tenant_id = r.tenant_id "
    "AND s.id = r.site_id WHERE r.tenant_id = :t AND (CAST(:s AS uuid) IS NULL OR r.site_id = CAST(:s AS uuid)) "
    "AND (CAST(:after AS timestamptz) IS NULL OR r.created_at > CAST(:after AS timestamptz)) "
    "ORDER BY r.created_at, r.id")

_UNLINKED = (
    "SELECT id, tenant_id, site_id, action_code, kind, origin_finding_id FROM chain_action "
    "WHERE thread_id IS NULL AND tenant_id = :t AND (CAST(:s AS uuid) IS NULL OR site_id = CAST(:s AS uuid)) "
    "ORDER BY kind, id")

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

    def sources(self, tenant_id: UUID, site_id: UUID | None = None, after: datetime | None = None) -> list[Source]:
        p = {"t": tenant_id, "s": None if site_id is None else str(site_id), "after": after}
        out = [finding_source(r) for r in self._rows(_FINDING_SOURCES, p)]
        out += [opportunity_source(r) for r in self._rows(_OPPORTUNITY_SOURCES, p)]
        return sorted(out, key=lambda s: (s.created_at, str(s.revision_id)))

    def unlinked_actions(self, tenant_id: UUID, site_id: UUID | None = None) -> list[dict[str, Any]]:
        return self._rows(_UNLINKED, {"t": tenant_id, "s": None if site_id is None else str(site_id)})

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
                tz, now = c.execute(text("SELECT s.timezone, now() FROM site s WHERE s.tenant_id = :t AND s.id = :s"),
                                    p).one()

                def rows(sql: str) -> list[dict[str, Any]]:
                    return [dict(r) for r in c.execute(text(sql), p).mappings()]

                out = {"tz": tz, "now": now, "action_events": rows(_ACTION_EVENTS), "outcomes": rows(_OUTCOMES),
                       "domain_actions": rows(_DOMAIN_ACTIONS), "case_completions": rows(_CASE_COMPLETIONS),
                       "finding_lifecycle": {r["finding_id"].lower(): r for r in rows(_FINDING_LIFECYCLE)},
                       "snapshots": []}
                if not c.execute(text("SELECT to_regclass('site_day_snapshot') IS NULL")).scalar_one():
                    out["snapshots"] = [_Snap(dict(r)) for r in c.execute(
                        text(_SNAPSHOTS), {"t": tenant_id, "sites": [str(site_id)], "m": measures}).mappings()]
        return out

    def opportunity_labels(self, tenant_id: UUID) -> dict[str, str]:
        rows = self._rows("SELECT id, public_no FROM mini_opportunity WHERE tenant_id = :t", {"t": tenant_id})
        return {str(r["id"]): f"OPP-{int(r['public_no']):06d}" for r in rows}

    def lookup(self, tenant_id: Any, finding_ids: Sequence[Any], action_ids: Sequence[Any], *,
               day: Any = None, known_at: datetime | None = None) -> dict[str, Any]:
        """CH-2 §5.2 / CH-3 §3, §5: one thread lookup per board, with each Finding's state on the board `day` as of
        `known_at`, and the COMPLETE days of its clean-day measures (CH-1a snapshots; none below 0043)."""
        from assetops_backend.chain.adapters.file_chain_config import load_thread_lifecycle
        from assetops_backend.chain.lifecycle import complete_days
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
                    complete = {fid: complete_days(snap, subject, policy.measures_for(mech))
                                for fid, (mech, subject) in subjects.items()}
        return thread_lookup(rows, day=day, known_at=known_at, complete=complete, close_after=policy.close_after())
