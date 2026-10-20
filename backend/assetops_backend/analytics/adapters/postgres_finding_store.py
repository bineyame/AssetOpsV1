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
from assetops_backend.analytics import ev
from assetops_backend.analytics.cold import plain
from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY
from assetops_backend.analytics.finding_episode import (
    DOMAIN,
    MATCHER_VERSION,
    MECHANISM,
    TITLES,
    Episode,
    Write,
)


#: W2-03 cold Finding identity: one mechanism and plain title per episode kind.
COLD_MATCHER_VERSION = "cold-episode/1"
COLD_MECHANISMS = {"EXCURSION": "COLD_EXCURSION", "START_RESPONSE": "COLD_START_FAILURE"}
COLD_TITLES = {"EXCURSION": "Cold room temperature outside its policy band",
               "START_RESPONSE": "Backup generator did not start when the grid failed"}


#: W2-06 Q15 EV interruption Finding: matcher version and the exact limitation sentences.
EV_MATCHER_VERSION = "1"
EV_LIMITATIONS = ("A connector fault and session abort were observed; component cause and unmet demand remain unknown.",
                  "Charger hardware failure, vehicle fault and lost revenue are not established by these records.")
EV_WITHDRAWN = "The current selected evidence no longer supports this interruption."


def _num(x) -> str:
    return format(float(x), ".4f")


class FindingStoreUnavailable(RuntimeError):
    pass


class FindingPinRefused(LookupError):
    """W3-01 q5: a pinned Finding revision is missing from this tenant/Site or was created after the cutoff."""

    def __init__(self, missing: list[str], later: list[str], known_at: datetime) -> None:
        super().__init__(f"Finding revision pins refused at {known_at.isoformat()}: missing {missing}, "
                         f"created after the cutoff {later}.")
        self.missing, self.later, self.known_at = missing, later, known_at


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
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, domain, revision_no, transition, "
            "lifecycle, claim_level, title, mechanism, matcher_version, analytic_id, model_version, "
            "assessment_revision_id, analytic_run_id, window_assessment_revision_id, episode_start, episode_end, "
            "candidate_minutes, necessary_minutes, indeterminate_minutes, claim, limitations, basis_sha256, "
            "support_sha256, cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:id, :t, :s, :f, "
            ":d, :n, :tr, :lc, :cl, :title, :m, :mv, :a, "
            ":model, :primary, :run, :wrev, :es, :ee, :cand, :nec, :ind, CAST(:claim AS jsonb), "
            "CAST(:limits AS jsonb), :basis, :support, :cited, :inputs, :now)"),
            {"id": rid, "t": tenant_id, "s": site_id, "f": w.finding_id, "d": DOMAIN, "n": number, "tr": w.transition,
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
            snap = self._index_snapshot(c, tenant_id, site_id, domain, analytic_id, None)
            del snap["selected_runs"]
            return {**snap, "fence": self._fence(c, tenant_id, site_id, analytic_id)}
        return self._read(work)

    def index_lineage(self, tenant_id: UUID, site_id: UUID, revision_ids: list[UUID]) -> dict[str, Any]:
        """Exact stored lineage of the selected immutable revisions on one index page: cited assessment
        revisions and runs (with their configuration selection) and cited accepted-evidence IDs."""
        return self._read(lambda c: self._index_lineage(c, tenant_id, site_id, revision_ids))

    # ---- W3-01 Run 5 (q5): the same reads on a caller-owned connection, at an explicit cutoff ----
    # None of these opens, begins or commits a transaction; the caller's REPEATABLE READ snapshot is the read.

    def fence_on(self, c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str) -> Fence:
        """The existing live writer fence on `c`. It is a current writer fence, not a historical matcher proof."""
        return self._fence(c, tenant_id, site_id, analytic_id)

    def index_snapshot_on(self, c: Connection, tenant_id: UUID, site_id: UUID, domain: str, analytic_id: str,
                          known_at: datetime) -> dict[str, Any]:
        """The Site Finding index as of `known_at`, on `c`: per Finding the latest revision created by then
        (stored `revision_no` orders the eligible revisions), merge links created by then, each window's latest
        selection by then (`selected_runs` names its run) and the latest pass of this matcher version completed
        by then, with that pass's deferred windows. No writer fence: see `fence_on`."""
        return {**self._index_snapshot(c, tenant_id, site_id, domain, analytic_id, known_at), "known_at": known_at}

    def index_lineage_on(self, c: Connection, tenant_id: UUID, site_id: UUID, revision_ids: list[UUID],
                         known_at: datetime) -> dict[str, Any]:
        """Exact stored lineage of exactly these pinned revisions, on `c`. Refuses (FindingPinRefused) when a
        pinned revision is missing from this tenant/Site or was created after `known_at`."""
        ids = [str(x) for x in revision_ids]
        found = {str(r[0]): r[1] for r in c.execute(text(
            "SELECT id, created_at FROM finding_revision WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[]))"), {"t": tenant_id, "s": site_id, "ids": ids})}
        missing = sorted(x for x in set(ids) if x not in found)
        later = sorted(x for x, at in found.items() if at > known_at)
        if missing or later:
            raise FindingPinRefused(missing, later, known_at)
        return self._index_lineage(c, tenant_id, site_id, revision_ids)

    @staticmethod
    def _index_snapshot(c: Connection, tenant_id: UUID, site_id: UUID, domain: str, analytic_id: str,
                        known_at: datetime | None) -> dict[str, Any]:
        p = {"t": tenant_id, "s": site_id, "d": domain, "a": analytic_id, "m": MATCHER_VERSION, "k": known_at}

        def by(column: str) -> str:
            return "" if known_at is None else f" AND {column} <= :k"
        heads = [dict(r._mapping) for r in c.execute(text(
            "SELECT DISTINCT ON (r.finding_id) r.finding_id, r.id AS finding_revision_id, r.revision_no, "
            "r.transition, r.lifecycle, r.claim_level, r.title, r.matcher_version, r.model_version, "
            "r.assessment_revision_id, r.analytic_run_id, r.window_assessment_revision_id, r.episode_start, "
            "r.episode_end, r.limitations, r.created_at AS revision_created_at, f.domain, f.analytic_id, "
            "f.cohort_sha256, f.anchor_start, f.recurs_after_finding_id, f.split_from_finding_id, "
            "(SELECT m.canonical_finding_id FROM finding_merge m WHERE m.tenant_id = f.tenant_id "
            f"AND m.superseded_finding_id = f.id{by('m.created_at')}) AS merged_into_finding_id "
            "FROM finding_revision r JOIN finding f ON f.id = r.finding_id "
            "WHERE f.tenant_id = :t AND f.site_id = :s AND f.domain = :d AND f.analytic_id = :a"
            f"{by('r.created_at')} ORDER BY r.finding_id, r.revision_no DESC"), p)]
        merges = [dict(r._mapping) for r in c.execute(text(
            "SELECT superseded_finding_id, canonical_finding_id, finding_revision_id FROM finding_merge "
            f"WHERE tenant_id = :t AND site_id = :s{by('created_at')} ORDER BY created_at, superseded_finding_id"), p)]
        selected = c.execute(text(
            "SELECT DISTINCT ON (window_start) window_start, seq, run_id FROM analytic_run_selection "
            f"WHERE tenant_id = :t AND site_id = :s AND analytic_id = :a{by('selected_at')} "
            "ORDER BY window_start, seq DESC"), p).all()
        row = c.execute(text("SELECT id, selection_seq, completed_at, deferred_window_starts "
                             "FROM finding_match_pass WHERE tenant_id = :t "
                             f"AND site_id = :s AND analytic_id = :a AND matcher_version = :m{by('completed_at')} "
                             "ORDER BY selection_seq DESC, completed_at DESC LIMIT 1"), p).one_or_none()
        deferred = [] if row is None else list(row[3] or [])
        match_pass = None if row is None else {"match_pass_id": str(row[0]), "matcher_version": MATCHER_VERSION,
                                               "matched_through_selection_seq": int(row[1]),
                                               "match_completed_at": row[2]}
        return {"heads": heads, "merges": merges, "selection_seqs": {r[0]: int(r[1]) for r in selected},
                "selected_runs": {r[0]: r[2] for r in selected}, "match_pass": match_pass,
                "deferred_windows": deferred}

    @staticmethod
    def _index_lineage(c: Connection, tenant_id: UUID, site_id: UUID, revision_ids: list[UUID]) -> dict[str, Any]:
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

    # --- cold_chain (W2-03): Findings on the cold worker's connection ----------------------------------------
    # `.agent/W2-03-build-spec.md` commit 3: this module alone inserts cold `finding`, `finding_revision`,
    # `finding_revision_assessment` and `finding_revision_evidence`, on the caller's transaction. The dispatch
    # `_insert_finding/_insert_revision` paths are untouched. A cold Finding carries `domain='cold_chain'`, its
    # `subject_asset_id`, NULL `generator_asset_id` and NULL dispatch minute fields; its claim names the exact
    # episode and episode revision.

    def cold_apply(self, c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str, persisted: dict[str, Any],
                   episodes: list[dict[str, Any]], limitations: list[str], now: datetime) -> list[UUID]:
        """Open, revise or withdraw the cold Finding of each episode revision written by this assessment."""
        written: list[UUID] = []
        for ep in episodes:
            if not ep["created"]:
                continue
            item, kind = ep["item"], ep["kind"]
            held = self._cold_finding_of(c, tenant_id, site_id, ep["episode_id"])
            warrants = item is not None and (item.exposure_finding if kind == "EXCURSION" else item.failure_finding)
            if ep["state"] == "NO_LONGER_SUPPORTED":
                if held is None:
                    continue
                transition, lifecycle = "NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED"
            elif held is None:
                if not warrants:
                    continue
                split = (None if ep["split_from_episode_id"] is None
                         else self._cold_finding_of(c, tenant_id, site_id, ep["split_from_episode_id"]))
                held = self._insert_cold_finding(c, tenant_id, site_id, analytic_id, ep, persisted,
                                                 None if split is None else split[0], now)
                transition, lifecycle = "OPENED", "SUPPORTED"
            else:
                transition = "SUPPORT_CHANGED" if ep["evidence_changed"] else "BASIS_REFRESHED"
                lifecycle = "SUPPORTED" if warrants else "UNCONFIRMED"
            rid = self._insert_cold_revision(c, tenant_id, site_id, analytic_id, held, ep, persisted, transition,
                                             lifecycle, limitations, now)
            if rid is not None:
                written.append(rid)
        return written

    @staticmethod
    def _cold_finding_of(c: Connection, tenant_id: UUID, site_id: UUID, episode_id: UUID):
        """(finding_id, mechanism, subject) of the cold Finding whose revisions claim `episode_id`, or None."""
        return c.execute(text(
            "SELECT f.id, f.mechanism, f.subject_asset_id FROM finding f JOIN finding_revision r ON r.finding_id = f.id "
            "WHERE f.tenant_id = :t AND f.site_id = :s AND f.domain = 'cold_chain' "
            "AND r.claim->>'episode_id' = :e ORDER BY r.revision_no LIMIT 1"),
            {"t": tenant_id, "s": site_id, "e": str(episode_id)}).first()

    @staticmethod
    def _insert_cold_finding(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str, ep: dict[str, Any],
                             persisted: dict[str, Any], split_from: UUID | None, now: datetime):
        fid = uuid4()
        mechanism = COLD_MECHANISMS[ep["kind"]]
        c.execute(text(
            "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
            "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, cohort_sha256, "
            "matcher_version, recurs_after_finding_id, split_from_finding_id, opened_at, created_at) VALUES "
            "(:id, :t, :s, :k, 'cold_chain', :m, :a, NULL, :subject, :anchor, :anchor_rev, NULL, :mv, NULL, "
            ":split, :now, :now)"),
            {"id": fid, "t": tenant_id, "s": site_id, "k": f"cold:{ep['kind']}:{ep['episode_id']}", "m": mechanism,
             "a": analytic_id, "subject": ep["subject_asset_id"], "anchor": ep["item"].anchor_time,
             "anchor_rev": persisted["revision_id"], "mv": COLD_MATCHER_VERSION, "split": split_from, "now": now})
        return (fid, mechanism, ep["subject_asset_id"])

    @staticmethod
    def _insert_cold_revision(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str, held,
                              ep: dict[str, Any], persisted: dict[str, Any], transition: str, lifecycle: str,
                              limitations: list[str], now: datetime) -> UUID | None:
        fid, mechanism = held[0], held[1]
        if c.execute(text("SELECT 1 FROM finding_revision WHERE finding_id = :f AND basis_sha256 = :b "
                          "AND transition = :tr"), {"f": fid, "b": persisted["basis"], "tr": transition}).first():
            return None  # this exact basis and transition is already recorded
        item, kind = ep["item"], ep["kind"]
        n = c.execute(text("SELECT coalesce(max(revision_no), 0) + 1 FROM finding_revision WHERE finding_id = :f"),
                      {"f": fid}).scalar_one()
        claim: dict[str, Any] = {"episode_id": str(ep["episode_id"]), "episode_revision_id": str(ep["revision_id"]),
                                 "kind": kind, "state": ep["state"]}
        start = end = None
        claim_level = "UNKNOWN"
        if item is not None:
            claim_level = item.claim_level
            if kind == "EXCURSION":
                start, end = item.start_latest, item.end_latest
                claim.update(plain({
                    "direction": item.direction, "start_bounds": {"earliest": item.start_earliest,
                                                                  "latest": item.start_latest},
                    "end_bounds": {"earliest": item.end_earliest, "latest": item.end_latest},
                    "duration_bounds": {"low": item.duration_low, "high": item.duration_high},
                    "degree_minute_bounds": {"low": item.degree_minutes_low, "high": item.degree_minutes_high},
                    "peak_observed": item.peak_observed, "open": item.open}))
            else:
                start = item.anchor_time
                claim.update(plain({"correlation_id": item.correlation_id, "result": item.result,
                                    "missing_steps": list(item.missing_steps),
                                    "start_timeout_min": item.start_timeout_min}))
        limits = list(limitations) + ([item.limitation] if item is not None and item.limitation else [])
        limits.append("No spoilage, product-loss or failed-part determination is made.")
        support = ep["support_ids"]
        digests = [r[0] for r in c.execute(text(
            "SELECT envelope_sha256 FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s AND id = ANY(:ids) "
            "ORDER BY id"), {"t": tenant_id, "s": site_id, "ids": support}).all()] if support else []
        rid = uuid4()
        c.execute(text(
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, domain, revision_no, transition, "
            "lifecycle, claim_level, title, mechanism, matcher_version, analytic_id, model_version, "
            "assessment_revision_id, analytic_run_id, window_assessment_revision_id, episode_start, episode_end, "
            "candidate_minutes, necessary_minutes, indeterminate_minutes, claim, limitations, basis_sha256, "
            "support_sha256, cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:id, :t, :s, :f, "
            "'cold_chain', :n, :tr, :life, :claim_level, :title, :m, :mv, :a, :model, :ar, :run, NULL, :es, :ee, "
            "NULL, NULL, NULL, CAST(:claim AS jsonb), CAST(:limits AS jsonb), :b, :sup, :cited, :input, :now)"),
            {"id": rid, "t": tenant_id, "s": site_id, "f": fid, "n": n, "tr": transition, "life": lifecycle,
             "claim_level": claim_level, "title": COLD_TITLES[kind], "m": mechanism, "mv": COLD_MATCHER_VERSION,
             "a": analytic_id, "model": "1", "ar": persisted["revision_id"], "run": persisted["run_id"],
             "es": start, "ee": end, "claim": json.dumps(claim), "limits": json.dumps(limits),
             "b": persisted["basis"], "sup": sha256_json(support), "cited": sha256_json(digests),
             "input": persisted["basis"], "now": now})
        c.execute(text(
            "INSERT INTO finding_revision_assessment (finding_revision_id, assessment_revision_id, tenant_id, site_id, "
            "analytic_run_id, scope, is_primary) VALUES (:r, :a, :t, :s, :run, 'WINDOW', true)"),
            {"r": rid, "a": persisted["revision_id"], "t": tenant_id, "s": site_id, "run": persisted["run_id"]})
        if support:
            c.execute(text("INSERT INTO finding_revision_evidence (finding_revision_id, evidence_id, tenant_id, "
                           "site_id) VALUES (:r, :e, :t, :s)"),
                      [{"r": rid, "e": e, "t": tenant_id, "s": site_id} for e in support])
        return rid

    # --- ev_charging (W2-06 commit 3, Q15): EV interruption Findings on the EV worker's connection --------------
    # This module alone inserts EV `finding`, `finding_revision`, `finding_revision_assessment` and
    # `finding_revision_evidence`, on the caller's transaction; it never inserts the EV session tables. A Finding
    # is opened only for an exact same-session START/FAULT/ABORT; a later basis without that support appends
    # NO_LONGER_SUPPORTED and keeps the Finding row and history.

    def ev_apply(self, c: Connection, inputs, sessions: list[dict[str, Any]], persisted: dict[str, Any],
                 now: datetime) -> list[UUID]:
        """Open, revise or withdraw the EV interruption Finding of each session of one new assessment revision,
        and withdraw a supported Finding anchored in the window whose session this basis no longer materializes."""
        t, s, w = inputs.tenant_id, inputs.site_id, inputs.window
        written: list[UUID] = []
        keys: set[str] = set()
        for row in sessions:
            session = row["session"]
            keys.add(session.finding_key_sha256)
            held = c.execute(text(
                "SELECT id FROM finding WHERE tenant_id = :t AND site_id = :s AND domain = 'ev_charging' "
                "AND finding_key = :k"), {"t": t, "s": s, "k": session.finding_key_sha256}).first()
            latest = None if held is None else self._ev_latest(c, t, s, held[0])
            if session.qualified_fault_abort:
                support = sorted(i for i, _ in session.finding_support)
                if held is None:
                    fid = uuid4()
                    c.execute(text(
                        "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
                        "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, "
                        "cohort_sha256, matcher_version, recurs_after_finding_id, split_from_finding_id, opened_at, "
                        "created_at) VALUES (:id, :t, :s, :k, 'ev_charging', :m, :a, NULL, :subject, :anchor, :ar, "
                        "NULL, :mv, NULL, NULL, :now, :now)"),
                        {"id": fid, "t": t, "s": s, "k": session.finding_key_sha256, "m": ev.MECHANISM,
                         "a": ev.SESSION_ANALYTIC, "subject": session.connector_asset_id, "anchor": session.start_at,
                         "ar": persisted["revision_id"], "mv": EV_MATCHER_VERSION, "now": now})
                    transition = "OPENED"
                else:
                    fid = held[0]
                    if latest is not None and latest["basis"] == persisted["basis"]:
                        continue  # this exact basis is already recorded
                    changed = latest is None or latest["support"] != support
                    transition = "SUPPORT_CHANGED" if changed else "BASIS_REFRESHED"
                claim = ev.plain({
                    "session_id": row["session_id"], "external_session_id": session.external_session_id,
                    "connector_asset_id": session.connector_asset_id, "start_at": session.start_at,
                    "abort_at": session.end_at, "fault_evidence_id": session.fault_evidence_id,
                    "supported_kwh": session.supported_kwh, "energy_complete": session.energy_complete})
                written.append(self._ev_revision(
                    c, t, s, fid, persisted, transition, "SUPPORTED", "OBSERVED", session.start_at, session.end_at,
                    claim, list(EV_LIMITATIONS), session.finding_support_sha256, support, now))
            elif latest is not None and latest["lifecycle"] == "SUPPORTED" and latest["basis"] != persisted["basis"]:
                written.append(self._ev_withdraw(c, t, s, held[0], latest, persisted, now))
        # A supported Finding anchored in this window whose session this basis no longer materializes.
        for fid, key in c.execute(text(
                "SELECT id, finding_key FROM finding WHERE tenant_id = :t AND site_id = :s AND domain = 'ev_charging' "
                "AND anchor_start >= :lo AND anchor_start < :hi ORDER BY anchor_start, id"),
                {"t": t, "s": s, "lo": w.from_at, "hi": w.to_at}).all():
            if key in keys:
                continue
            latest = self._ev_latest(c, t, s, fid)
            if latest is not None and latest["lifecycle"] == "SUPPORTED" and latest["basis"] != persisted["basis"]:
                written.append(self._ev_withdraw(c, t, s, fid, latest, persisted, now))
        return written

    @staticmethod
    def _ev_latest(c: Connection, t: UUID, s: UUID, finding_id: UUID) -> dict[str, Any] | None:
        row = c.execute(text(
            "SELECT id, lifecycle, basis_sha256, episode_start, episode_end, claim, limitations FROM finding_revision "
            "WHERE tenant_id = :t AND site_id = :s AND finding_id = :f ORDER BY revision_no DESC LIMIT 1"),
            {"t": t, "s": s, "f": finding_id}).first()
        if row is None:
            return None
        support = sorted(str(e) for e in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND finding_revision_id = :r"), {"t": t, "s": s, "r": row[0]}).scalars())
        claim = row[5] if isinstance(row[5], dict) else json.loads(row[5])
        return {"id": row[0], "lifecycle": row[1], "basis": row[2], "start": row[3], "end": row[4], "claim": claim,
                "support": support}

    def _ev_withdraw(self, c: Connection, t: UUID, s: UUID, finding_id: UUID, latest: dict[str, Any],
                     persisted: dict[str, Any], now: datetime) -> UUID:
        """NO_LONGER_SUPPORTED: identity and last supported bounds kept; fault, quantity and completeness null; no
        support links."""
        claim = {**latest["claim"], "fault_evidence_id": None, "supported_kwh": None, "energy_complete": None}
        return self._ev_revision(c, t, s, finding_id, persisted, "NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED",
                                 "UNKNOWN", latest["start"], latest["end"], claim,
                                 list(EV_LIMITATIONS) + [EV_WITHDRAWN], ev.EMPTY_SUPPORT_SHA256, [], now)

    @staticmethod
    def _ev_revision(c: Connection, t: UUID, s: UUID, finding_id: UUID, persisted: dict[str, Any],
                     transition: str, lifecycle: str, claim_level: str, start: datetime, end: datetime,
                     claim: dict[str, Any], limitations: list[str], support_sha: str, support: list[str],
                     now: datetime) -> UUID:
        n = c.execute(text("SELECT coalesce(max(revision_no), 0) + 1 FROM finding_revision WHERE tenant_id = :t "
                           "AND site_id = :s AND finding_id = :f"), {"t": t, "s": s, "f": finding_id}).scalar_one()
        rid = uuid4()
        c.execute(text(
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, domain, revision_no, transition, "
            "lifecycle, claim_level, title, mechanism, matcher_version, analytic_id, model_version, "
            "assessment_revision_id, analytic_run_id, window_assessment_revision_id, episode_start, episode_end, "
            "candidate_minutes, necessary_minutes, indeterminate_minutes, claim, limitations, basis_sha256, "
            "support_sha256, cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:id, :t, :s, :f, "
            "'ev_charging', :n, :tr, :life, :claim_level, :title, :m, :mv, :a, :model, :ar, :run, NULL, :es, :ee, "
            "NULL, NULL, NULL, CAST(:claim AS jsonb), CAST(:limits AS jsonb), :b, :sup, :sup, :b, :now)"),
            {"id": rid, "t": t, "s": s, "f": finding_id, "n": n, "tr": transition, "life": lifecycle,
             "claim_level": claim_level, "title": ev.FINDING_TITLE, "m": ev.MECHANISM, "mv": EV_MATCHER_VERSION,
             "a": ev.SESSION_ANALYTIC, "model": ev.MODEL_VERSION, "ar": persisted["revision_id"],
             "run": persisted["run_id"], "es": start, "ee": end, "claim": json.dumps(claim),
             "limits": json.dumps(limitations), "b": persisted["basis"], "sup": support_sha, "now": now})
        c.execute(text(
            "INSERT INTO finding_revision_assessment (finding_revision_id, assessment_revision_id, tenant_id, site_id, "
            "analytic_run_id, scope, is_primary) VALUES (:r, :a, :t, :s, :run, 'WINDOW', true)"),
            {"r": rid, "a": persisted["revision_id"], "t": t, "s": s, "run": persisted["run_id"]})
        if support:
            c.execute(text("INSERT INTO finding_revision_evidence (finding_revision_id, evidence_id, tenant_id, "
                           "site_id) VALUES (:r, :e, :t, :s)"),
                      [{"r": rid, "e": e, "t": t, "s": s} for e in support])
        return rid
