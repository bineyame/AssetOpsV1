"""PostgreSQL Finding store (S4-01 phase 1, migration 0009).

The fifth product database writer (architecture guard rule 8): it only INSERTs
its own append-only tables. Writes for one Site run in one transaction under a
Site-scoped advisory lock and re-check the selection/job fence the matcher read
under, so a selection that lands between the read and the write is never
half-applied: the caller re-plans instead. Revisions are append-only and immutable
(`finding_revision_no_unique`); replay is idempotent against the Finding's latest revision only
(`_insert_revision`), so a basis may return (A -> B -> A, migration 0015) and append a new revision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from assetops_backend.analytics.assessment_inputs import sha256_json
from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY
from assetops_backend.analytics.finding_episode import (
    DOMAIN,
    MATCHER_VERSION,
    MECHANISM,
    TITLES,
    Episode,
    Write,
)


def _num(x) -> str:
    return format(float(x), ".4f")


class FindingStoreUnavailable(RuntimeError):
    pass


class FindingFenceMoved(RuntimeError):
    """A selection or recompute job changed between the matcher's read and its write."""


@dataclass(frozen=True)
class Fence:
    selection_seq: int
    job_count: int
    job_marker: str
    finding_revisions: int = 0


@dataclass(frozen=True)
class Applied:
    finding_ids: tuple[str, ...]
    revision_ids: tuple[str, ...]


class PostgresFindingStore:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise FindingStoreUnavailable("DATABASE_URL is not set, so the Finding store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def _read(self, work):
        try:
            with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise FindingStoreUnavailable(f"The Finding store failed: {error.orig}") from error

    @staticmethod
    def _fence(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str) -> Fence:
        seq = c.execute(text("SELECT coalesce(max(seq), 0) FROM analytic_run_selection WHERE tenant_id = :t "
                             "AND site_id = :s AND analytic_id = :a"),
                        {"t": tenant_id, "s": site_id, "a": analytic_id}).scalar_one()
        count, marker = c.execute(text(
            "SELECT count(*), coalesce(max(created_at)::text, '') || '/' || "
            "coalesce(string_agg(status, ',' ORDER BY id), '') FROM recompute_job WHERE tenant_id = :t "
            "AND site_id = :s"), {"t": tenant_id, "s": site_id}).one()
        # Finding state is part of the fence: a pass planned before another pass committed (whose episodes
        # are stale) must re-plan instead of opening a second Finding for the same episode. Revisions are
        # append-only, so their count only grows.
        revisions = c.execute(text("SELECT count(*) FROM finding_revision WHERE tenant_id = :t AND site_id = :s"),
                              {"t": tenant_id, "s": site_id}).scalar_one()
        return Fence(int(seq), int(count), marker, int(revisions))

    def fence(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> Fence:
        return self._read(lambda c: self._fence(c, tenant_id, site_id, analytic_id))

    def assessed_days(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> list[date]:
        rows = self._read(lambda c: c.execute(text(
            "SELECT DISTINCT window_start FROM analytic_run_selection WHERE tenant_id = :t AND site_id = :s "
            "AND analytic_id = :a ORDER BY window_start"), {"t": tenant_id, "s": site_id, "a": analytic_id}).all())
        return [r[0].date() for r in rows]

    def episodes(self, tenant_id: UUID, site_id: UUID) -> list[Episode]:
        rows = self._read(lambda c: c.execute(text(
            "SELECT DISTINCT ON (f.id) f.id, f.generator_asset_id, f.anchor_start, r.lifecycle, r.episode_start, "
            "r.episode_end, r.basis_sha256, r.model_version, r.support_sha256, "
            "(SELECT o.claim -> 'recurrence' FROM finding_revision o WHERE o.finding_id = f.id "
            "ORDER BY o.revision_no LIMIT 1) FROM finding f "
            "JOIN finding_revision r "
            "ON r.finding_id = f.id WHERE f.tenant_id = :t AND f.site_id = :s ORDER BY f.id, r.revision_no DESC"),
            {"t": tenant_id, "s": site_id}).all())
        return [Episode(str(r[0]), r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]) for r in rows]

    def apply(self, tenant_id: UUID, site_id: UUID, analytic_id: str, writes: list[Write], fence: Fence,
              now: datetime, *, deferred: Iterable[datetime] = ()) -> Applied:
        def work(c: Connection) -> Applied:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtext('finding:' || :s))"), {"s": str(site_id)})
            if self._fence(c, tenant_id, site_id, analytic_id) != fence:
                raise FindingFenceMoved("a selection, recompute job or Finding changed since the matcher read; "
                                        "re-plan")
            findings, revisions = [], []
            for w in writes:
                if w.new_finding is not None:
                    self._insert_finding(c, tenant_id, site_id, analytic_id, w, now)
                    findings.append(w.finding_id)
                rid = self._insert_revision(c, tenant_id, site_id, analytic_id, w, now)
                if rid is not None:
                    revisions.append(rid)
            # Q18: the pass itself is recorded, so "no Finding" can cite a completed match at that selection.
            # The windows it deferred (a group touching a missing or non-CURRENT window within the continuity
            # margin) are recorded on it: the pass did not match them, so `match_state` keeps them pending.
            c.execute(text("INSERT INTO finding_match_pass (id, tenant_id, site_id, analytic_id, selection_seq, "
                           "matcher_version, revisions_written, completed_at, deferred_window_starts) VALUES "
                           "(:id, :t, :s, :a, :seq, :matcher, :n, :now, CAST(:deferred AS timestamptz[]))"),
                      {"id": uuid4(), "t": tenant_id, "s": site_id, "a": analytic_id, "seq": fence.selection_seq,
                       "matcher": MATCHER_VERSION, "n": len(revisions), "now": now,
                       "deferred": sorted(deferred)})
            return Applied(tuple(findings), tuple(revisions))

        try:
            with self._connect().begin() as c:
                return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise FindingStoreUnavailable(f"The Finding store failed: {error.orig}") from error

    @staticmethod
    def _insert_finding(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str, w: Write,
                        now: datetime) -> None:
        n = w.new_finding or {}
        c.execute(text(
            "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
            "generator_asset_id, anchor_start, anchor_assessment_revision_id, cohort_sha256, matcher_version, "
            "recurs_after_finding_id, split_from_finding_id, opened_at, created_at) VALUES (:id, :t, :s, :k, :d, "
            ":m, :a, :g, :anchor, :anchor_rev, :cohort, :mv, :recurs, :split, :now, :now)"),
            {"id": w.finding_id, "t": tenant_id, "s": site_id, "k": n["finding_key"], "d": DOMAIN, "m": MECHANISM,
             "a": analytic_id, "g": w.asset, "anchor": n["anchor_start"],
             "anchor_rev": n["anchor_assessment_revision_id"], "cohort": n["cohort_sha256"], "mv": MATCHER_VERSION,
             "recurs": n["recurs_after_finding_id"], "split": n["split_from_finding_id"], "now": now})

    @staticmethod
    def _insert_revision(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str, w: Write,
                         now: datetime) -> str | None:
        # Replay guard against the LATEST revision only (LR-01): a basis that returns to an earlier one (proof
        # recorded then revoked: run B -> run C -> run B) is a new revision, never swallowed by an older match.
        exists = c.execute(text("SELECT 1 FROM (SELECT basis_sha256, transition FROM finding_revision "
                                "WHERE finding_id = :f ORDER BY revision_no DESC LIMIT 1) x "
                                "WHERE x.basis_sha256 = :b AND x.transition = :tr"),
                           {"f": w.finding_id, "b": w.basis_sha256, "tr": w.transition}).first()
        if exists:
            return None
        digests = c.execute(text(
            "SELECT id::text, envelope_sha256 FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[])) ORDER BY id"),
            {"t": tenant_id, "s": site_id, "ids": w.cited_evidence_ids}).all()
        if len(digests) != len(w.cited_evidence_ids):
            raise FindingFenceMoved("a cited evidence ID is not accepted in this Site")
        number = c.execute(text("SELECT coalesce(max(revision_no), 0) + 1 FROM finding_revision "
                                "WHERE finding_id = :f"), {"f": w.finding_id}).scalar_one()
        rid = str(uuid4())
        c.execute(text(
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, revision_no, transition, lifecycle, "
            "claim_level, title, mechanism, matcher_version, analytic_id, model_version, assessment_revision_id, "
            "analytic_run_id, window_assessment_revision_id, episode_start, episode_end, candidate_minutes, "
            "necessary_minutes, indeterminate_minutes, claim, limitations, basis_sha256, support_sha256, "
            "cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:id, :t, :s, :f, :n, :tr, :lc, "
            ":cl, :title, :m, :mv, :a, "
            ":model, :primary, :run, :wrev, :es, :ee, :cand, :nec, :ind, CAST(:claim AS jsonb), "
            "CAST(:limits AS jsonb), :basis, :support, :cited, :inputs, :now)"),
            {"id": rid, "t": tenant_id, "s": site_id, "f": w.finding_id, "n": number, "tr": w.transition,
             "lc": w.lifecycle, "cl": w.claim_level, "title": TITLES[w.lifecycle], "m": MECHANISM,
             "mv": MATCHER_VERSION, "a": analytic_id, "model": w.model_version, "primary": w.primary_revision_id,
             "run": w.primary_run_id, "wrev": w.window_revision_id, "es": w.episode_start, "ee": w.episode_end,
             "cand": _num(w.minutes[CANDIDATE]), "nec": _num(w.minutes[NECESSARY]),
             "ind": _num(w.minutes[INDETERMINATE]), "claim": json.dumps(w.claim, sort_keys=True),
             "limits": json.dumps(w.limitations), "basis": w.basis_sha256, "support": w.support_sha256,
             "cited": sha256_json([[r[0], r[1]] for r in digests]), "inputs": sha256_json(w.input_sha256s),
             "now": now})
        for revision_id, run_id, scope, primary in w.assessments:
            c.execute(text(
                "INSERT INTO finding_revision_assessment (finding_revision_id, assessment_revision_id, tenant_id, "
                "site_id, analytic_run_id, scope, is_primary) VALUES (:r, :a, :t, :s, :run, :scope, :p)"),
                {"r": rid, "a": revision_id, "t": tenant_id, "s": site_id, "run": run_id, "scope": scope,
                 "p": primary})
        for evidence_id in w.cited_evidence_ids:
            c.execute(text(
                "INSERT INTO finding_revision_evidence (finding_revision_id, evidence_id, tenant_id, site_id) "
                "VALUES (:r, :e, :t, :s)"), {"r": rid, "e": evidence_id, "t": tenant_id, "s": site_id})
        if w.merged_into is not None:
            c.execute(text(
                "INSERT INTO finding_merge (superseded_finding_id, canonical_finding_id, tenant_id, site_id, "
                "finding_revision_id, created_at) VALUES (:old, :new, :t, :s, :r, :now)"),
                {"old": w.finding_id, "new": w.merged_into, "t": tenant_id, "s": site_id, "r": rid, "now": now})
        return rid

    def rows(self, tenant_id: UUID, site_id: UUID) -> dict[str, Any]:
        """Every Finding and revision of a Site, for verification and the phase-2 read."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id}
            findings = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding WHERE tenant_id = :t AND site_id = :s ORDER BY anchor_start, id"), p)]
            revisions = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_revision WHERE tenant_id = :t AND site_id = :s "
                "ORDER BY finding_id, revision_no"), p)]
            cites = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_revision_assessment WHERE tenant_id = :t AND site_id = :s"), p)]
            evidence = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s"), p)]
            merges = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_merge WHERE tenant_id = :t AND site_id = :s"), p)]
            return {"findings": findings, "revisions": revisions, "assessments": cites, "evidence": evidence,
                    "merges": merges}
        return self._read(work)

    # ---- S4-01 phase 2: exact Finding root / revision read (read-only) ----

    def finding_detail(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any] | None:
        """One Finding root under its tenant and Site, every immutable revision with its cited assessment
        revisions (and their runs), and the stored relations. None for a foreign or unknown ID."""
        def work(c: Connection) -> dict[str, Any] | None:
            p = {"t": tenant_id, "s": site_id, "f": finding_id}
            row = c.execute(text("SELECT * FROM finding WHERE tenant_id = :t AND site_id = :s AND id = :f"), p).first()
            if row is None:
                return None
            revisions = [dict(r._mapping) for r in c.execute(text(
                "SELECT r.*, (SELECT count(*) FROM finding_revision_evidence e WHERE e.finding_revision_id = r.id) "
                "AS cited_evidence_count FROM finding_revision r WHERE r.tenant_id = :t AND r.site_id = :s "
                "AND r.finding_id = :f ORDER BY r.revision_no"), p)]
            cites = [dict(r._mapping) for r in c.execute(text(
                "SELECT a.finding_revision_id, a.assessment_revision_id, a.analytic_run_id, a.scope, a.is_primary, "
                "v.window_start, v.window_end, v.claim_level, v.assessment_key, v.revision_no, v.model_version, "
                "ar.foundation_revision_ids, ar.binding_set_revision_ids "
                "FROM finding_revision_assessment a JOIN finding_revision r ON r.id = a.finding_revision_id "
                "JOIN analytic_run ar ON ar.id = a.analytic_run_id "
                "JOIN assessment_revision v ON v.id = a.assessment_revision_id WHERE r.tenant_id = :t "
                "AND r.site_id = :s AND r.finding_id = :f ORDER BY a.scope DESC, v.window_start, "
                "a.assessment_revision_id"), p)]
            for rev in revisions:
                rev["assessments"] = [x for x in cites if x["finding_revision_id"] == rev["id"]]
            relations = {
                "merged_into": [dict(r._mapping) for r in c.execute(text(
                    "SELECT * FROM finding_merge WHERE tenant_id = :t AND site_id = :s "
                    "AND superseded_finding_id = :f"), p)],
                "merged_from": [dict(r._mapping) for r in c.execute(text(
                    "SELECT * FROM finding_merge WHERE tenant_id = :t AND site_id = :s "
                    "AND canonical_finding_id = :f ORDER BY created_at, superseded_finding_id"), p)],
                "split_parts": [x for (x,) in c.execute(text(
                    "SELECT id FROM finding WHERE tenant_id = :t AND site_id = :s AND split_from_finding_id = :f "
                    "ORDER BY anchor_start, id"), p)],
                "recurred_by": [x for (x,) in c.execute(text(
                    "SELECT id FROM finding WHERE tenant_id = :t AND site_id = :s AND recurs_after_finding_id = :f "
                    "ORDER BY anchor_start, id"), p)],
            }
            return {"finding": dict(row._mapping), "revisions": revisions, "relations": relations}

        return self._read(work)

    def revision_lineage(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID,
                         off_bounds: list[tuple[str, str]]) -> dict[str, Any]:
        """The selected revision's cited accepted evidence (exact stored IDs), the analytic runs it cites, and
        the accepted generator OFF reports placed at each `(assessment_revision_id, iso time)` bound."""
        from assetops_backend.analytics.adapters.postgres_assessment_store import _evidence

        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id, "r": finding_revision_id}
            ids = [x for (x,) in c.execute(text(
                "SELECT evidence_id FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s "
                "AND finding_revision_id = :r"), p)]
            runs = [dict(r._mapping) for r in c.execute(text(
                "SELECT id, analytic_id, model_version, window_start, window_end, knowledge_cutoff, input_sha256, "
                "cohort_status, cohort_sha256, configuration_sha256, foundation_revision_ids, "
                "binding_set_revision_ids, watermarks, completed_at, (SELECT count(*) FROM analytic_run_evidence "
                "x WHERE x.run_id = analytic_run.id) AS input_evidence_count FROM analytic_run "
                "WHERE tenant_id = :t AND site_id = :s AND id IN (SELECT analytic_run_id FROM "
                "finding_revision_assessment WHERE finding_revision_id = :r) ORDER BY window_start, id"), p)]
            offs = []
            for revision_id, at in off_bounds:
                found = [x for (x,) in c.execute(text(
                    "SELECT e.id FROM assessment_revision v JOIN accepted_evidence e ON e.tenant_id = v.tenant_id "
                    "AND e.site_id = v.site_id AND e.id::text IN (SELECT jsonb_array_elements_text(v.evidence_ids)) "
                    "WHERE v.tenant_id = :t AND v.site_id = :s AND v.id = :v AND e.role IN "
                    "('generator_state', 'generator_power') AND (e.source_time = :at OR e.interval_start = :at "
                    "OR e.interval_end = :at) ORDER BY e.id"),
                    {**p, "v": UUID(revision_id), "at": datetime.fromisoformat(at.replace("Z", "+00:00"))})]
                offs.append({"assessment_revision_id": revision_id, "at": at, "evidence_ids": found})
            return {"evidence": _evidence(c, tenant_id, site_id, ids), "runs": runs, "off_reports": offs}

        return self._read(work)

    # ---- S4-03 phase 1: Finding Evidence / History reads (read-only) ----

    def revision_evidence(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID) -> dict[str, Any]:
        """The selected revision's complete cited set (`finding_revision_evidence`) with every recorded lineage
        column, and the size of the run input set it is distinct from. Joins are LEFT so a cited ID whose accepted
        row, batch, disposition or basis does not resolve is reported, never silently dropped. The envelope
        digest is recomputed in SQL (SHA-256 over the stored text's UTF-8 bytes, as acceptance computed it)."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id, "r": finding_revision_id}
            rows = [dict(r._mapping) for r in c.execute(text(
                "SELECT x.evidence_id AS cited_evidence_id, e.id AS evidence_id, e.envelope_sha256, "
                "e.envelope_text IS NOT NULL AND e.envelope_text <> '' AS envelope_present, "
                "encode(sha256(convert_to(e.envelope_text, 'UTF8')), 'hex') = e.envelope_sha256 AS envelope_digest_ok, "
                "e.message_id, e.batch_id, b.id AS batch_found, b.external_batch_id, e.gateway_id, "
                "e.source_id, e.sequence_epoch, e.sequence, e.device_id, e.signal_id, e.role, e.asset_id, "
                "e.source_time, e.interval_start, e.interval_end, e.published_at, e.received_at, "
                "d.decided_at AS accepted_at, d.decision AS disposition, "
                "d.accepted_evidence_id AS disposition_evidence_id, "
                "e.quality, e.unavailable_reason, e.normalized_value_text AS value, e.normalized_unit AS unit, "
                "e.source_mode, e.conversion_kind, e.configuration_outdated, e.foundation_revision_id, "
                "fr.id AS foundation_found, fr.version AS foundation_version, e.binding_set_revision_id, "
                "bs.id AS binding_set_found, bs.version AS binding_set_version, e.binding_revision_id, "
                "br.id AS binding_found "
                "FROM finding_revision_evidence x "
                "LEFT JOIN accepted_evidence e ON e.tenant_id = x.tenant_id AND e.site_id = x.site_id "
                "AND e.id = x.evidence_id "
                "LEFT JOIN ingestion_batch b ON b.tenant_id = e.tenant_id AND b.site_id = e.site_id "
                "AND b.id = e.batch_id "
                "LEFT JOIN ingestion_disposition d ON d.tenant_id = e.tenant_id AND d.site_id = e.site_id "
                "AND d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                "LEFT JOIN foundation_revision fr ON fr.tenant_id = e.tenant_id AND fr.site_id = e.site_id "
                "AND fr.id = e.foundation_revision_id "
                "LEFT JOIN signal_binding_set_revision bs ON bs.tenant_id = e.tenant_id AND bs.site_id = e.site_id "
                "AND bs.id = e.binding_set_revision_id "
                "LEFT JOIN signal_binding_revision br ON br.tenant_id = e.tenant_id AND br.site_id = e.site_id "
                "AND br.id = e.binding_revision_id "
                "WHERE x.tenant_id = :t AND x.site_id = :s AND x.finding_revision_id = :r "
                "ORDER BY e.source_time NULLS LAST, x.evidence_id"), p)]
            ids = [r["cited_evidence_id"] for r in rows]
            used: dict[str, list[str]] = {}
            for eid, aid in c.execute(text(
                    "SELECT x.eid, a.assessment_revision_id::text FROM finding_revision_assessment a "
                    "JOIN assessment_revision v ON v.tenant_id = a.tenant_id AND v.site_id = a.site_id "
                    "AND v.id = a.assessment_revision_id "
                    "CROSS JOIN LATERAL jsonb_array_elements_text(v.evidence_ids) AS x(eid) "
                    "WHERE a.tenant_id = :t AND a.site_id = :s AND a.finding_revision_id = :r "
                    "AND x.eid = ANY(:ids) ORDER BY 1, 2"), {**p, "ids": [str(i) for i in ids]}):
                used.setdefault(eid, []).append(aid)
            inputs: dict[str, list[str]] = {}
            for eid, rid in c.execute(text(
                    "SELECT x.evidence_id::text, x.run_id::text FROM analytic_run_evidence x WHERE x.tenant_id = :t "
                    "AND x.site_id = :s AND x.run_id IN (SELECT analytic_run_id FROM finding_revision_assessment "
                    "WHERE finding_revision_id = :r) AND x.evidence_id = ANY(:ids) ORDER BY 1, 2"),
                    {**p, "ids": ids}):
                inputs.setdefault(eid, []).append(rid)
            for r in rows:
                key = str(r["cited_evidence_id"])
                r["cited_by_assessment_revision_ids"] = used.get(key, [])
                r["input_of_run_ids"] = inputs.get(key, [])
            distinct_inputs = c.execute(text(
                "SELECT count(DISTINCT x.evidence_id) FROM analytic_run_evidence x WHERE x.tenant_id = :t "
                "AND x.site_id = :s AND x.run_id IN (SELECT analytic_run_id FROM finding_revision_assessment "
                "WHERE finding_revision_id = :r)"), p).scalar_one()
            return {"rows": rows, "distinct_input_evidence_count": int(distinct_inputs)}

        return self._read(work)

    def revision_times(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, dict[str, Any]]:
        """Per revision of one Finding: its cited set's source-time span, latest receipt and acceptance time, the
        resolved cited count, and the latest completion of the analytic runs it cites. Distinct time kinds."""
        def work(c: Connection) -> dict[str, dict[str, Any]]:
            p = {"t": tenant_id, "s": site_id, "f": finding_id}
            out = {str(r["id"]): dict(r) for r in (x._mapping for x in c.execute(text(
                "SELECT r.id, count(x.evidence_id) AS cited, count(e.id) AS cited_resolved, "
                "min(e.source_time) AS source_first, max(e.source_time) AS source_last, "
                "max(e.received_at) AS received_latest, max(d.decided_at) AS accepted_latest "
                "FROM finding_revision r LEFT JOIN finding_revision_evidence x ON x.tenant_id = r.tenant_id "
                "AND x.site_id = r.site_id AND x.finding_revision_id = r.id "
                "LEFT JOIN accepted_evidence e ON e.tenant_id = x.tenant_id AND e.site_id = x.site_id "
                "AND e.id = x.evidence_id "
                "LEFT JOIN ingestion_disposition d ON d.tenant_id = e.tenant_id AND d.site_id = e.site_id "
                "AND d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                "WHERE r.tenant_id = :t AND r.site_id = :s AND r.finding_id = :f GROUP BY r.id"), p))}
            for rid, done in c.execute(text(
                    "SELECT a.finding_revision_id::text, max(ar.completed_at) FROM finding_revision_assessment a "
                    "JOIN finding_revision r ON r.id = a.finding_revision_id JOIN analytic_run ar "
                    "ON ar.tenant_id = a.tenant_id AND ar.site_id = a.site_id AND ar.id = a.analytic_run_id "
                    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.finding_id = :f GROUP BY 1"), p):
                if rid in out:
                    out[rid]["analytic_completed_latest"] = done
            return out

        return self._read(work)

    def match_state(self, tenant_id: UUID, site_id: UUID, analytic_id: str, window_start: datetime
                    ) -> dict[str, Any]:
        """The window's current selection sequence and the latest completed pass of this matcher version. The
        window is matched only when that pass ran at or after its selection and did not defer it."""
        def work(c: Connection) -> dict[str, Any]:
            seq = c.execute(text("SELECT max(seq) FROM analytic_run_selection WHERE tenant_id = :t AND site_id = :s "
                                 "AND analytic_id = :a AND window_start = :w"),
                            {"t": tenant_id, "s": site_id, "a": analytic_id, "w": window_start}).scalar_one()
            row = c.execute(text("SELECT id, selection_seq, completed_at, :w = ANY(deferred_window_starts) "
                                 "FROM finding_match_pass WHERE tenant_id = :t "
                                 "AND site_id = :s AND analytic_id = :a AND matcher_version = :m "
                                 "ORDER BY selection_seq DESC, completed_at DESC LIMIT 1"),
                            {"t": tenant_id, "s": site_id, "a": analytic_id, "m": MATCHER_VERSION,
                             "w": window_start}).one_or_none()
            deferred = row is not None and bool(row[3])
            return {"window_selection_seq": seq, "matcher_version": MATCHER_VERSION,
                    "match_pass_id": None if row is None else str(row[0]),
                    "matched_through_selection_seq": None if row is None else row[1],
                    "match_completed_at": None if row is None else row[2],
                    "match_deferred": deferred,
                    "matched": seq is not None and row is not None and row[1] >= seq and not deferred}
        return self._read(work)

    def findings_over(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime) -> list[dict[str, Any]]:
        """Latest revision of every Finding whose latest bounds overlap [lo, hi), with its cited window IDs."""
        def work(c: Connection) -> list[dict[str, Any]]:
            rows = [dict(r._mapping) for r in c.execute(text(
                "SELECT DISTINCT ON (r.finding_id) r.finding_id, r.id AS revision_id, r.lifecycle, r.transition, "
                "r.episode_start, r.episode_end FROM finding_revision r WHERE r.tenant_id = :t AND r.site_id = :s "
                "ORDER BY r.finding_id, r.revision_no DESC"), {"t": tenant_id, "s": site_id})]
            rows = [r for r in rows if r["episode_start"] < hi and lo <= r["episode_end"]]
            for r in rows:
                r["window_assessment_revision_ids"] = [x for (x,) in c.execute(text(
                    "SELECT assessment_revision_id FROM finding_revision_assessment WHERE finding_revision_id = :r "
                    "AND scope = 'WINDOW' ORDER BY assessment_revision_id"), {"r": r["revision_id"]})]
            return sorted(rows, key=lambda r: (r["episode_start"], str(r["finding_id"])))

        return self._read(work)

    # ---- S4-04 phase 1: Site Finding index (read-only; `findings_over` above is left unchanged) ----

    def index_snapshot(self, tenant_id: UUID, site_id: UUID, domain: str, analytic_id: str) -> dict[str, Any]:
        """One REPEATABLE READ snapshot for the Site Finding index: the latest revision of every Finding of
        this domain/analytic with its merge, split and recurrence links, every window's current selection
        sequence, the latest completed pass of this matcher version, and the writer fence."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id, "d": domain, "a": analytic_id, "m": MATCHER_VERSION}
            heads = [dict(r._mapping) for r in c.execute(text(
                "SELECT DISTINCT ON (r.finding_id) r.finding_id, r.id AS finding_revision_id, r.revision_no, "
                "r.transition, r.lifecycle, r.claim_level, r.title, r.matcher_version, r.model_version, "
                "r.assessment_revision_id, r.analytic_run_id, r.window_assessment_revision_id, r.episode_start, "
                "r.episode_end, r.limitations, r.created_at AS revision_created_at, f.domain, f.analytic_id, "
                "f.cohort_sha256, f.anchor_start, f.recurs_after_finding_id, f.split_from_finding_id, "
                "(SELECT m.canonical_finding_id FROM finding_merge m WHERE m.tenant_id = f.tenant_id "
                "AND m.superseded_finding_id = f.id) AS merged_into_finding_id "
                "FROM finding_revision r JOIN finding f ON f.id = r.finding_id "
                "WHERE f.tenant_id = :t AND f.site_id = :s AND f.domain = :d AND f.analytic_id = :a "
                "ORDER BY r.finding_id, r.revision_no DESC"), p)]
            merges = [dict(r._mapping) for r in c.execute(text(
                "SELECT superseded_finding_id, canonical_finding_id, finding_revision_id FROM finding_merge "
                "WHERE tenant_id = :t AND site_id = :s ORDER BY created_at, superseded_finding_id"), p)]
            seqs = {r[0]: int(r[1]) for r in c.execute(text(
                "SELECT window_start, max(seq) FROM analytic_run_selection WHERE tenant_id = :t AND site_id = :s "
                "AND analytic_id = :a GROUP BY window_start"), p)}
            row = c.execute(text("SELECT id, selection_seq, completed_at FROM finding_match_pass WHERE tenant_id = :t "
                                 "AND site_id = :s AND analytic_id = :a AND matcher_version = :m "
                                 "ORDER BY selection_seq DESC, completed_at DESC LIMIT 1"), p).one_or_none()
            match_pass = None if row is None else {"match_pass_id": str(row[0]), "matcher_version": MATCHER_VERSION,
                                                   "matched_through_selection_seq": int(row[1]),
                                                   "match_completed_at": row[2]}
            return {"heads": heads, "merges": merges, "selection_seqs": seqs, "match_pass": match_pass,
                    "fence": self._fence(c, tenant_id, site_id, analytic_id)}
        return self._read(work)

    def index_lineage(self, tenant_id: UUID, site_id: UUID, revision_ids: list[UUID]) -> dict[str, Any]:
        """Exact stored lineage of the selected immutable revisions on one index page: cited assessment
        revisions and runs (with their configuration selection) and cited accepted-evidence IDs."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id, "ids": [str(x) for x in revision_ids]}
            cites = [dict(r._mapping) for r in c.execute(text(
                "SELECT finding_revision_id, assessment_revision_id, analytic_run_id, scope, is_primary "
                "FROM finding_revision_assessment WHERE tenant_id = :t AND site_id = :s "
                "AND finding_revision_id = ANY(CAST(:ids AS uuid[])) ORDER BY scope DESC, assessment_revision_id"), p)]
            evidence = [dict(r._mapping) for r in c.execute(text(
                "SELECT finding_revision_id, evidence_id FROM finding_revision_evidence WHERE tenant_id = :t "
                "AND site_id = :s AND finding_revision_id = ANY(CAST(:ids AS uuid[])) ORDER BY evidence_id"), p)]
            runs = [dict(r._mapping) for r in c.execute(text(
                "SELECT id, model_version, input_sha256, configuration_sha256, cohort_sha256, "
                "foundation_revision_ids, binding_set_revision_ids, knowledge_cutoff FROM analytic_run "
                "WHERE tenant_id = :t AND site_id = :s AND id IN (SELECT analytic_run_id FROM "
                "finding_revision_assessment WHERE finding_revision_id = ANY(CAST(:ids AS uuid[]))) "
                "ORDER BY window_start, id"), p)]
            return {"assessments": cites, "evidence": evidence, "runs": runs}
        return self._read(work)
